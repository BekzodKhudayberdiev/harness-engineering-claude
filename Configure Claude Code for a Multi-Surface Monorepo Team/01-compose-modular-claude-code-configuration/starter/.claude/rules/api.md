---
description: Conventions for Node.js API handlers and middleware
paths:
  - "src/api/**/*"
---

# API handler rules

Loads when editing any file under `src/api/`.

## Handler function shape

- Every handler is a named `async` function that takes `(req: Request, res: Response)` and returns `{ status: number, body: any }`.
- Do not write directly to `res.send()` or `res.json()` — the framework adapter handles serialization after the handler returns.
- This pattern keeps handlers unit-testable without HTTP mocking.

## Error handling

- For expected failures (validation, auth, not-found), throw `ApiError(status, code, message)` with the appropriate HTTP status.
- Never throw raw `Error(...)` from handler code — that becomes a 500 and obscures the actual problem.
- Always add context to errors: use `ApiError(500, "DB_ERROR", "Failed to fetch order: " + e.message)` instead of re-throwing.

## Request validation

- Validate request bodies at the boundary using Zod schemas from `src/api/_schemas/`.
- Do not re-validate downstream in service functions — the handler is the validation boundary.

## Response contracts

- Response bodies must match schemas defined in `src/api/_schemas/responses/`.
- If you need to add a field to a response, update the schema in the same commit — no unschemaed responses.
