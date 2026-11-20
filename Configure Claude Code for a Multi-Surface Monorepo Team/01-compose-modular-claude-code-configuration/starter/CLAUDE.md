# E-Commerce Platform — Shared Claude Code Conventions

This file is the **project-level** entry point for the e-commerce monorepo. Every teammate's Claude session loads it automatically.

## Scope: what belongs here vs. elsewhere

| Scope | Location | Shared? | Example |
|-------|----------|---------|---------|
| **Project-level** | `./CLAUDE.md`, `.claude/` | ✅ Via Git | Team coding standards, shared rules for React/API/tests |
| **User-level** | `~/.claude/` | ❌ Not versioned | Your preferred commit message style, local LLM settings |
| **Directory-level** | `subdir/CLAUDE.md` | ✅ Via Git | Monorepo subdirectory-specific overrides (if needed) |

**Note:** User-level settings in `~/.claude/` are NOT shared with teammates via version control — they're personal to each developer's machine.

This hierarchy keeps team conventions synchronized (project-level), respects individual workflows (user-level), and enables subdirectory customization without fragmenting the monorepo.

## Shared standards (modular via @-imports)

The actual conventions live in focused files so this entry point stays scannable:

@.claude/standards/frontend.md
@.claude/standards/api.md
@.claude/standards/database.md
@.claude/standards/testing.md

Path-scoped rules in [.claude/rules/](.claude/rules/) layer on top of these standards and activate only when Claude is editing matching files (React components, API handlers, test files).

## Repository layout

```
src/components/   React components (functional + hooks)
src/pages/        Top-level routes
src/api/          Node.js API handlers
src/db/           PostgreSQL repository-pattern modules
```

Tests are co-located: `Foo.tsx` lives next to `Foo.test.tsx`.

## Troubleshooting

If a CLAUDE.md instruction isn't being followed, run `/memory` to see exactly which configuration files actually loaded for your current session.

## Team workflows

- `/review <pr-ref>` — codified PR review checklist. (You will author this in Exercise 2.)
- `/deploy-check` — read-only pre-deployment validation. (You will author this in Exercise 3.)

For decisions about when to use plan mode vs. direct execution on this codebase, you will produce a team decision doc in Exercise 4.
