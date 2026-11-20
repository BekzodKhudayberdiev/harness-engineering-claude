"""Anti-pattern audit.

Verifies, by static AST analysis, that the agentic loop does NOT:
- use string-membership tests against text content to drive control flow
- use an integer-literal iteration cap as its primary stopping mechanism
- omit reference to `stop_reason` as the loop-breaking signal

And that the package broadly does not branch on `claim_type` equality
outside of the tool-schema definitions and the cost-estimate module.

Each test parses the relevant file with `ast` and walks the tree. There are
no runtime imports of claims_intake here — the audit is static, so it works
even if loop.py / tools.py do not run end-to-end.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "claims_intake"
LOOP_PY = PKG / "loop.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ---------------------------------------------------------------------------
# Anti-pattern 1 — no string-membership tests against assistant text in the loop
# ---------------------------------------------------------------------------
def test_no_string_membership_against_text_in_loop() -> None:
    """No `"some_token" in <something>` expressions in loop.py.

    Heuristic: any `ast.Compare` node using `ast.In` whose `left` operand is a
    string `ast.Constant` is flagged. The loop has no legitimate reason to test
    for the presence of a magic string inside the model's output — that would be
    natural-language-driven control flow.
    """
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # Check if this Compare has an ast.In operator and left operand is a string Constant
            if any(isinstance(op, ast.In) for op in node.ops):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    offenders.append(ast.unparse(node))

    assert offenders == [], f"Found string-membership tests in loop.py:\n" + "\n".join(offenders)


# ---------------------------------------------------------------------------
# Anti-pattern 2 — no integer-literal iteration cap as the primary stop mechanism
# ---------------------------------------------------------------------------
def test_no_integer_literal_iteration_cap_in_loop() -> None:
    """No `for _ in range(<int literal>)` and no `while <var> < <int literal>` in loop.py.

    Token/wall-clock/config-sourced budgets are explicitly allowed because they
    read their cap from a `Budget` instance (an attribute access or a function
    arg), not from a literal. If you need a cap, pass it in.
    """
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        # Check for `for _ in range(<int literal>, ...)`
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                    # Check if any arg is an int Constant
                    for arg in node.iter.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                            offenders.append(ast.unparse(node))
                            break

        # Check for `while <var> < <int literal>`
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Compare):
                for comparator in node.test.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, int):
                        offenders.append(ast.unparse(node.test))
                        break

    assert offenders == [], f"Found integer-literal iteration caps in loop.py (use a Budget instead):\n" + "\n".join(offenders)


# ---------------------------------------------------------------------------
# Positive evidence — stop_reason is the value that breaks the while loop
# ---------------------------------------------------------------------------
def test_stop_reason_is_loop_control() -> None:
    """loop.py references `stop_reason` AND a `while` loop exits via return/raise on it."""
    tree = _parse(LOOP_PY)

    # Check 1: Assert there is at least one reference to `stop_reason`
    has_stop_reason_ref = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "stop_reason":
            has_stop_reason_ref = True
            break
        if isinstance(node, ast.Name) and node.id == "stop_reason":
            has_stop_reason_ref = True
            break

    assert has_stop_reason_ref, "loop.py must reference `stop_reason`"

    # Check 2: Find at least one while loop that exits on stop_reason
    found_proper_exit = False
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            body_text = ast.unparse(node)
            # Check if body mentions both "stop_reason" and ("return" or "raise")
            if "stop_reason" in body_text and ("return" in body_text or "raise" in body_text):
                found_proper_exit = True
                break

    assert found_proper_exit, "loop.py must have a while loop that exits via return/raise on stop_reason"


# ---------------------------------------------------------------------------
# Decision-tree-in-Python — no `if claim_type == "..."` branches in the package
# ---------------------------------------------------------------------------
def test_no_claim_type_equality_branching_in_package() -> None:
    """Decision logic about claim type lives in the model, not in Python.

    tools.py is exempt (it defines the enum in input_schema).
    pricing.py is exempt (it may map claim_type to per-queue cost weights).
    """
    offenders = []
    exempted_files = {"tools.py", "pricing.py", "__init__.py"}

    # Walk every .py file under PKG
    for py_file in PKG.rglob("*.py"):
        if py_file.name in exempted_files:
            continue

        tree = _parse(py_file)

        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Check if operators include Eq
                if any(isinstance(op, ast.Eq) for op in node.ops):
                    # Check if left operand is Name or Attribute named "claim_type"
                    is_claim_type = False
                    if isinstance(node.left, ast.Name) and node.left.id == "claim_type":
                        is_claim_type = True
                    elif isinstance(node.left, ast.Attribute) and node.left.attr == "claim_type":
                        is_claim_type = True

                    # Check if any comparator is a string Constant
                    if is_claim_type:
                        for comparator in node.comparators:
                            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                                rel_path = py_file.relative_to(PKG.parent)
                                offenders.append(f"{rel_path}:{node.lineno}: {ast.unparse(node)}")

    assert offenders == [], f"Decision logic for claim_type must live in the model, not Python. Move to tool calls:\n" + "\n".join(offenders)
