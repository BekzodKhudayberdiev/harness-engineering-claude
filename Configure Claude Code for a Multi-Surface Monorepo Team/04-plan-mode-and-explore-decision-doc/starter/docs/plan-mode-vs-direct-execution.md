# Plan mode vs. direct execution — team decision guide

Choosing between Claude Code's **plan mode** (investigate and propose before changing anything) and **direct execution** (change code immediately) is the single biggest leverage point in how the team uses the harness day-to-day. The wrong mode at either extreme costs us: plan mode for trivial fixes is friction; direct execution for architectural changes burns context and produces rework.

> Anchor talk: Knight-Webb, "SWE Is Becoming Plan and Review."

This doc walks four concrete decisions against our codebase: one plan-mode example, one direct-execution example, one Explore-subagent example, and one combined-workflow example.

---

## 1. Plan-mode example

**Task:** Extract a shared `useCart(userId)` hook from three React components to reduce duplication and improve testability.

**Files affected:** `src/components/Cart/Cart.tsx`, `src/components/Checkout/Checkout.tsx`, and `src/components/MiniCart/MiniCart.tsx` currently each implement the same cart-data-fetching pattern. The extraction target is a new custom hook in src/hooks/.

**Why plan mode:**
- **Multi-file refactor:** Three components need coordinated changes.
- **Multiple valid approaches:** Should the hook manage loading state? Should it fetch on mount or on-demand? These architectural questions need a proposal before coding.
- **API shape debate:** The extracted hook's signature (params, return type) affects all three call sites.

**Plan-mode flow:** Use plan mode to investigate the three components, propose the hook signature, identify edge cases (error handling, re-fetching), and get team agreement on the design. Once the plan is approved, direct execution applies the mechanical changes. This approach prevents costly rework: if the first sketch of the API proves awkward halfway through the refactor, we've wasted less effort because we thought it through first.

---

## 2. Direct-execution example

**Task:** Add a `min: 0` validation to the quantity field in `src/api/_schemas/orders.ts` to prevent negative order quantities.

**Why direct execution:**
- **Single function:** One validation schema, one line changed.
- **Known diff:** You already predict what Claude will do (add `.min(0)` to the quantity field).
- **Low risk:** Schema validation is non-invasive; test suite will catch any slip.

**Direct-execution flow:** You invoke Claude directly with something like: "In `src/api/_schemas/orders.ts`, add `.min(0)` to the quantity field validator." Claude makes the one-line change, you review, done. No plan needed because you've already thought through the solution. Skipping plan mode here saves context and friction.

---

## 3. Explore-subagent example

**Task:** Inventory every call site of the `processRefund` function to understand the refund flow and identify if there are edge cases in ordering or error handling.

**Why Explore subagent:**
- **Discovery-heavy:** You need to search across `src/api/orders/refund.ts`, `src/api/billing/issue.ts`, and `src/services/payment.ts` to find all usages.
- **Verbose intermediate output:** Grep results, diffs, inline analysis — none of that belongs in the main conversation. Only the final inventory matters.
- **Context preservation:** The Explore sub-agent runs in an isolated session and returns a summary, keeping the main conversation lean.

**Explore-subagent flow with scratchpad pattern:** Invoke the Explore sub-agent with the discovery task. It searches for `processRefund` call sites, documents them in a scratchpad (e.g., `tmp/refund-callsites.md`), and isolates the verbose discovery output and returns a structured summary of the findings: "Three call sites found. Issue.ts calls it after charging, refund.ts calls it after DB update, payment.ts calls it in a background job." The scratchpad pattern ensures the full inventory survives beyond the sub-agent's context window, so you can reference it later.

---

## 4. Combined workflow — plan mode for investigation, then direct execution

**Task:** Rename `ordersRepo.findById` → `ordersRepo.getById` in `src/db/orders.ts` to align with the team naming convention (get* for single-row reads, find* for multi-row queries).

**Why combined workflow:**
- **Investigation before mechanics:** You don't yet know all the call sites. `findById` might appear in handlers, services, and tests — some dynamically constructed (e.g., string interpolation in generated SQL). Grep alone may miss edge cases.
- **Mechanical changes are trivial once you know the scope:** Once plan mode has inventoried every call site and ruled out dynamic lookups, the actual rename is keystrokes: replace `findById` with `getById` in the repository and all call sites, then run tests.
- **Combining modes saves rework:** Diving straight into find-and-replace might miss a dynamic lookup or leave a stale comment. Plan mode catches that upfront.

**Combined workflow — 3-step flow:**
1. **Plan mode (investigate and propose):** Invoke plan mode with: "Rename `ordersRepo.findById` → `ordersRepo.getById` in `src/db/orders.ts`. Are there any call sites? Are any of them dynamic (not literal `findById` strings)?" Plan mode searches `src/api/`, `src/services/`, and test files. It documents every call site (handler in orders/create.ts, service in orders/fetch.ts, mock in orders.test.ts) and confirms all are literal function calls, not dynamic. It then proposes the rename: change function signature in orders.ts, then update all three call sites. You review and approve.

2. **Approval:** You review the plan and confirm the call-site list is exhaustive and the approach is sound.

3. **Direct execution (apply changes and validate):** You invoke Claude directly: "Apply the rename: change `findById` to `getById` in src/db/orders.ts, then update call sites in src/api/orders/create.ts, src/services/orders/fetch.ts, and src/orders.test.ts. Run the test suite." Claude makes the four-file change, runs tests, done.

---

## Quick reference

| Situation | Mode |
|-----------|------|
| Single function, fix is obvious, you can predict the diff | Direct execution |
| Multi-file refactor, API shape is debatable | Plan mode |
| Discovery / inventory across the codebase, you'll throw away the intermediate steps | Explore subagent |
| Investigation-then-mechanical-change | Plan mode → direct execution |
| Architectural decision (which database, which queue) | Plan mode, possibly with a fork to compare options |

When in doubt: plan mode is recoverable (you can switch to execution), but direct execution on a complex change is not. Default to plan when uncertain.
