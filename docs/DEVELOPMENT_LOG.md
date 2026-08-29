# Development Log
## Skeleton (production structure)
- Layered pi/ (FastAPI), authN/AuthZ first (JWT + API key → Principal; RBAC + agent scopes), request-id/tenant/rate middleware, error model, structured logging.
- Tested pure logic: policy engine, payment state machine (UNKNOWN first-class), protocol gateway (no money action), idempotency, cart guards, atomic campaign budget, refund guard, JWT auth, rate limiting, purchase flow.
- CI: lint/type/unit/compile/OpenAPI/secrets; integration + frontend non-blocking (to verify).
Next: docs/49-engineering-phases.md.
