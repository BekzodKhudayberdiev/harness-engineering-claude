---
description: Conventions for unit and integration tests
paths:
  - "**/*.test.tsx"
  - "**/*.test.ts"
---

# Test file rules

Loads when editing any `*.test.ts` or `*.test.tsx` file, layering on top of React or API rules as applicable.

## Test scope and naming

- One logical test suite per file: group related tests under a single `describe` block named after the unit being tested.
- Test names are descriptive sentences: `"should validate order total before submission"` not `"test 1"`.
- If a test file is testing a component or handler, name the test file to match: `Cart.tsx` pairs with `Cart.test.tsx`.

## Assertions and test helpers

- Use assertion library consistently across the team (not mixing Chai, Jest matchers, and Node assertions).
- For component tests, assert on rendered output and user interactions, not internal hook state or memoization.
- For API handler tests, call the handler function directly with a request shape — never spin up the HTTP layer.

## Forbidden patterns

- **No snapshots** — snapshots hide intent and clutter diffs. Write explicit assertions.
- **No `setTimeout` or fake timers** — if the test needs timing control, refactor the code to inject time.
- **No database mocking** — integration tests hit a real PostgreSQL test instance. Mocking the DB layer is forbidden — we got burned by a mocked test that hid a broken migration.
