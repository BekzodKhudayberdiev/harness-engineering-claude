"""Three invocation shapes.

thin     — prompt only.
rich     — hot state + new defects.
resumed  — prior partial findings + new defects since the last manifest step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .state import HotState

InvocationShape = Literal["thin", "rich", "resumed"]


@dataclass(frozen=True)
class Invocation:
    shape: InvocationShape
    prompt: str


def thin(prompt: str) -> Invocation:
    return Invocation(shape="thin", prompt=prompt)


def rich(
    role: str, hot_state: HotState, new_defects: Sequence[Mapping[str, Any]]
) -> Invocation:
    lines = [
        f"You are the on-call {role} for Northridge Plant 3.",
        "",
        "## Current hot state",
        f"Recent defect hashes: {hot_state.recent_defect_hashes}",
        f"Summary: {hot_state.current_shift_summary}",
        f"Active alerts: {hot_state.active_alerts}",
        f"Threshold statuses: {hot_state.threshold_statuses}",
        "",
        "## New defects since last shift",
    ]

    if new_defects:
        for defect in new_defects:
            lines.append(
                f"- {defect['id']} ({defect['ts']}, shift {defect['shift']}): "
                f"{defect['component']} / {defect['severity']} / {defect['description']}"
            )
    else:
        lines.append("(none)")

    lines.extend([
        "",
        "Please provide:",
        "1. Summary of the current shift state",
        "2. Key findings from new defects",
        "3. Recommended actions",
        "4. An updated hot state proposal as a JSON block with keys: "
        "current_shift_summary, active_alerts, threshold_statuses",
    ])

    prompt = "\n".join(lines)
    return Invocation(shape="rich", prompt=prompt)


def resumed(
    session_id: str,
    summary: str,
    latest_message: str,
    prior_steps: Sequence[Mapping[str, Any]],
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    lines = [
        f"Session: {session_id}",
        "",
        "## Prior partial findings",
    ]

    if prior_steps:
        for step in prior_steps:
            payload_repr = str(step.get("payload", {}))[:50]
            lines.append(f"- {step.get('name', '?')}: {payload_repr}")
    else:
        lines.append("(none)")

    lines.extend([
        "",
        "## Prior summary",
        summary,
        "",
        "## New defects since last partial step",
    ])

    if new_defects:
        for defect in new_defects:
            lines.append(
                f"- {defect['id']} ({defect['ts']}): "
                f"{defect.get('component', '?')} / {defect.get('severity', '?')} / "
                f"{defect.get('description', '')}"
            )
    else:
        lines.append("- (none)")

    lines.extend([
        "",
        "## Latest instruction",
        latest_message,
    ])

    prompt = "\n".join(lines)
    return Invocation(shape="resumed", prompt=prompt)
