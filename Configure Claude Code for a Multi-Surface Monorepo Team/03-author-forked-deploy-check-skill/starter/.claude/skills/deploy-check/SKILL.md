---
name: deploy-check
description: Pre-deployment validation checklist (read-only, runs in a forked sub-agent)
context: fork
argument-hint: "[target-branch] (defaults to main)"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
---

# /deploy-check

Runs the team's pre-deployment validation checklist against the current working tree and the branch you're about to ship. Read-only by design — this skill never modifies files, never pushes, never deploys. It returns a single structured summary so the calling session can decide whether to proceed.

## Why this is a skill (not a CLAUDE.md addition)

**Skill:** Invoked on-demand right before a deploy, runs in a forked sub-agent. Produces verbose intermediate output (file diffs, check logs, full status traces) that only matters during the deployment decision.

**CLAUDE.md:** Always-loaded in every session. Carries conventions that must be present for all editing work (e.g. "tests are co-located", "throw ApiError for validation failures").

**Rule:** On-demand + forked + task-specific → skill. Always-loaded + universal → CLAUDE.md. This keeps the main session lean and reserves the fork for intensive, one-time checks.

## Why `context: fork`

The goal is to keep verbose intermediate output out of the main session. A deploy check walks the working tree, enumerates files, parses diffs, and runs multiple validation passes — all of that chatter has no value to the calling session once the verdict is known. Only the structured summary (pass/fail + three check results) should return to the conversation.

`context: fork` is a Claude Code product feature operating at the skill-invocation layer, conceptually analogous to the *Branching Reality* pattern: establish a shared starting point (the current working tree), then branch into an isolated exploration (the forked sub-agent) whose verbose working output never flows back into the parent. Session-level forking (`fork_session`) applies the same pattern to a whole session; skill forking applies it at task granularity.

## Checks

Run all three. Each check produces a pass-or-fail verdict; if any fails, the overall summary is **fail**.

### Check 1 — Working tree clean

**Detect:** Run `git status --porcelain` — if it returns any lines, there are uncommitted changes.

**Pass:** `git status --porcelain` returns empty. Everything is committed.

**Fail:** One or more files are staged, unstaged, or untracked. Output: `uncommitted files detected: <list first 5 files, omit rest>`.

### Check 2 — Database migrations up-to-date

**Detect:** Parse `git diff main...HEAD --name-only` for files matching `src/db/repositories/*.ts`. For each new or modified repository import, search the diff for a corresponding migration file in `src/db/migrations/` with the same intent (file name or migration comment must reference the repository).

**Pass:** Every new repository import or DB-related change is backed by a migration file committed in the same PR.

**Fail:** A repository was added/modified without a migration. Output: `migrations missing for: <repo file>; add migration or revert change`.

### Check 3 — CI checks passing on open PR

**Detect:** Run `gh pr view --json statusCheckRollup` — report the status of all required checks.

**Pass:** All required GitHub Status Checks are marked SUCCESS.

**Fail:** One or more required checks are FAILURE, PENDING, or missing. Output: `CI checks not passing: <failed-check-names>`.

## Output format

Return exactly this shape to the main session:

```
verdict: pass | fail
checks:
  - name: <check-name>
    status: pass | fail
    detail: <one line or empty>
```

Do not include the raw `git status`, raw diff hunks, or full check logs in the returned summary — those stay in the fork. If the author wants to investigate a failed check, they can re-invoke the skill targeting that single check or run the underlying command themselves.

## Personalization

This skill is project-scoped (`.claude/skills/deploy-check/`) so the whole team gets the same checks. If a teammate wants a stricter variant — for example, one that additionally fails when a diff exceeds 500 lines without a detailed PR description — they can create a parallel skill at `~/.claude/skills/deploy-check-strict/SKILL.md` with a different name. Their variant will not be committed to the repo and will not affect teammates.

## What this skill deliberately does not do

- It never pushes, deploys, or runs migrations. The `allowed-tools` allowlist is read-only by construction; even if a future maintainer adds `Write` here, the team's `/review` command should catch the change.
- It does not run the test suite. Tests have their own pre-merge gate in CI; duplicating that here would slow every deploy check without adding signal.
- It does not check for secrets in code. That's the job of the `gitleaks` pre-commit hook, which fails the commit, not the deploy.
