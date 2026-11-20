---
description: Conduct code review against conventions and standards
argument-hint: "PR reference (e.g., main..feature-branch) or file path to review"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
  - Bash(gh pr diff:*)
---

# /review — team PR review

You are reviewing the diff identified by `$ARGUMENTS` against this repository's conventions. Apply the path-scoped rules in `.claude/rules/` (they auto-load based on the files touched) and the shared standards in `.claude/standards/`.

## Phase 1 — Interview pattern

Before reporting findings on ambiguous changes, ask clarifying questions. Without this step, you risk confidently wrong verdicts: for example, flagging "no test coverage" on a refactor when the behavior was already covered upstream. The author shouldn't have to argue against a false positive.

**Interview triggers:** Ask before reporting on these patterns:

1. **Dependency changes** — package.json or pyproject.toml diffs. The author may have pinned a new version as a one-line emergency fix. Ask: "Did this dependency change require the other diffs?"

2. **Public API or DB shape changes** — adding/removing/renaming response fields or columns. These often come with migrations or coordinated frontend updates. Ask: "Is this change part of a larger refactoring that spans multiple PRs?"

3. **Refactors with no test changes** — moving code, extracting functions, restructuring modules without adding new tests. Ask: "Is this a pure refactor of already-covered behavior, or does it introduce new logic?"

4. **Multi-surface changes** — diffs that touch API handlers, React components, and DB migrations all at once. Ask: "What's the narrative connecting these three changes?"

## Phase 2 — Review criteria

**Must report** (block the merge if serious):

- **Bugs**: Missing `await`, race conditions, off-by-one errors, unhandled promise rejections, logic errors that break the feature.
- **Security**: Raw SQL with user input, missing auth checks, hardcoded secrets, `dangerouslySetInnerHTML`, missing CSRF tokens.
- **Convention violations**: Violations of the team standards (`.claude/standards/`) or path-scoped rules (`.claude/rules/`). Examples: throwing raw `Error` instead of `ApiError`, using `useLayoutEffect` outside `src/hooks/`, writing directly to `res.json()` in a handler.
- **Breaking changes**: Removing fields from public API responses, DB column removals without migration, changing function signatures in exported modules.
- **Migration safety**: Migrations that lock the table, missing rollback, adding NOT NULL columns without defaults.

**Skip** (don't block; let the author decide):

- **Formatting**: Prettier diffs, indentation, whitespace. The linter handles this.
- **Naming bikeshed**: "Should this be `fetchOrders` vs. `getOrders`?" if the name is reasonable and the constant is not shared across the team.
- **Personal style**: "I prefer early returns" or "I prefer nested conditions" when neither is a team rule.
- **TODO comments**: "TODO: add memoization" if there's already a tracking ticket or a Jira link in the comment.
- **Non-blocking improvements**: Nice-to-haves that don't fix bugs or prevent future bugs ("consider extracting a helper" when the code works fine as-is).

## Phase 3 — Bundling: interacting vs. independent findings

**Interacting findings** share a single fix. Bundle them into ONE message with full context so the author can fix both at once.

Example: A handler is missing both an `await` on a database call AND a transaction wrapper around that same call. Report these together: "refundOrder needs a transaction wrapping the payment and DB writes, and the await on the payment call." The author fixes both changes on the same lines.

**Independent findings** have separate fixes. Report them SEQUENTIALLY as discrete items so each is actionable in isolation.

Example: One handler is missing an `await`, and a different handler uses raw SQL instead of the repository. These are separate functions — report each finding standalone. The author can fix them in any order.

**One-line heuristic**: If fixing issue A changes code that issue B references, they're interacting. If the fixes don't touch the same lines, they're independent.

## Phase 4 — Output format

For each finding, produce:

```
[severity] path/to/file.ts:line
finding: <one-sentence description>
fix: <one-sentence recommendation>
```

Severity is `bug` | `security` | `convention` | `breaking`. End with a one-line verdict: `approve`, `comment`, or `request-changes`.

## Examples

**Example 1 — Independent findings**

**Input:** Diff from `src/api/orders/handler.ts`

```typescript
export async function getOrder(req: Request) {
  const orderId = req.query.id;
  const result = pool.query(`SELECT * FROM orders WHERE id = ${orderId}`);
  return { status: 200, body: { order: result } };
}
```

**Output:** Report two separate findings

```
[convention] src/api/orders/handler.ts:3
finding: Handler uses raw SQL query with user input (orderId).
fix: Use OrderRepository.getById(orderId) from src/db/repositories/OrderRepository.ts instead.

[convention] src/api/orders/handler.ts:4
finding: Response body shape does not match defined schema; should be `{ orders: [...] }` not `{ order: {...} }`.
fix: Check src/api/_schemas/responses/OrderResponse.ts and align the response shape; update schema if needed.

Verdict: request-changes
```

---

**Example 2 — Interacting findings**

**Input:** Diff from `src/api/payments/refundOrder.ts`

```typescript
export async function refundOrder(req: Request) {
  const { orderId, amount } = req.body;
  const refundResult = paymentService.refund(orderId, amount);  // Missing await
  const dbResult = pool.query(`UPDATE orders SET status = 'refunded' WHERE id = ${orderId}`);  // Raw SQL, no transaction
  return { status: 200, body: { refunded: true } };
}
```

**Output:** Report one bundled finding

```
[bug] src/api/payments/refundOrder.ts:3–5
finding: refundOrder has three interacting issues: (1) missing await on paymentService.refund, (2) no transaction wrapping the payment and DB writes, (3) raw SQL query instead of OrderRepository. If the payment service call fails but the SQL succeeds, the order is marked refunded without actual refund — data corruption.
fix: Wrap the payment and DB calls in a transaction using withTransaction(async (tx) => ...) from src/db/tx.ts. Use OrderRepository.updateStatus(orderId, 'refunded') instead of raw SQL. Await the payment call before updating the DB.

Verdict: request-changes
```

## Notes

- This command is project-scoped (`.claude/commands/review.md`) so everyone on the team gets the same review. If you want to layer personal preferences (e.g. a stricter accessibility check on your own PRs), put a `~/.claude/commands/review-strict.md` in your home directory — it will not affect teammates.
- If a finding requires running code or modifying files to verify, ask the author to run a specific check rather than attempting it from the review session. This command's `allowed-tools` are read-only by design.
