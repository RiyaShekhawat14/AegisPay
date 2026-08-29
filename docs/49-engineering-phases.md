# 49 — Engineering Phases

A pragmatic, reject-proofing build plan. Each phase is independently valuable and gated by
its own exit criteria. AuthN/AuthZ comes first so nothing is built without a real identity
and tenant boundary. Every phase ends green (lint, type, tests) and is CI-locked.

## Current state
The layered skeleton + tested pure logic is in place: auth (JWT/API-key → Principal + RBAC +
agent scopes), rate limiting, request-id/tenant middleware, error model, and the tested
**purchase flow** (idempotent payment, timeout → UNKNOWN, deduped webhook, reconcile → PAID).
The gaps are DB-backed execution, real provider HTTP, observability, and turning
integration/e2e/red-team into required checks.

```
api/
├── main.py        # mounts middleware, error handlers, v1 router
├── config/ core/  # settings, exceptions, security(JWT/API-key), authorization(RBAC+ABAC), idempotency, ratelimit, db(RLS)
├── dependencies/  # auth, tenant, db-session, rate
├── middleware/    # request_id, tenant_context, rate_limit
├── routers/       # controllers (health, me, then carts/orders/payments…)
├── schemas/       # pydantic DTOs
├── policy/ graph/ # policy engine; LangGraph proposal layer
├── services/ repositories/ websockets/  # service layer (Ph 3), DB repos (Ph 2), sessions (planned)
├── modules/       # implemented domain (commerce, payments, gateway, campaigns, …)
├── ai_runtime/    # isolated AI runtime (no DB, no secrets, no money tools)
└── tests/         # unit, integration, fixtures
```

## Phase 1 — Identity, Authentication & Authorization
**Goal:** a real trust boundary; nothing runs without an authenticated, scoped, tenant-bound principal.
- Deliver: JWT (HS256) + API-key auth → `Principal(subject, type, tenant, role)`; RBAC for
  dashboard users; scoped permissions (ABAC) for agents (never money tools); rate limiting;
  request-id + tenant-context middleware; structured logging with `request_id/tenant`.
- Files: `api/core/{security,jwt,authorization,ratelimit,exceptions,logging}.py`,
  `api/middleware/*`, `api/dependencies/auth.py`, `tests/unit/test_{jwt,authorization,ratelimit}.py`.
- Exit: all of the above green + CI; `/v1/me` returns the principal.

## Phase 2 — Data layer (PostgreSQL)
**Goal:** durable, tenant-isolated storage wired to the app.
- Deliver: SQLAlchemy async models mirroring `migrations/0001_init.sql`; `DeclarativeBase` +
  timestamps; `BaseRepo` (tenant-scoped via `SET LOCAL app.tenant_id`); a session dependency;
  repositories per aggregate (orders, payments, campaigns). RLS stays in the DB (two roles).
- Files: `app/db/{base.py, session.py, repositories/*.py}`, `api/dependencies/auth.py` (db session),
  `tests/integration/*` (real Postgres).
- Exit: migration applies cleanly; a tenant-scoped repo test proves A cannot read B.

## Phase 3 — Commerce execution path (SELL)
**Goal:** create-cart → order → authorize → pay actually persists and transitions.
- Deliver: services for cart/order/payment using repositories; cart hash + price version +
  inventory reservation + expiry; transaction-bound, expiring, single-use authorization;
  guard that cart/price/inventory changes invalidate authorization.
- Files: `api/modules/commerce/*` (services), `api/routers/{carts,orders,payments}.py`.
- Exit: end-to-end create → order → authorize persists; e2e green.

## Phase 4 — Payment safety (provider + reconcile + webhook + refund)
**Goal:** provider truth, no double-charge, UNKNOWN handled.
- Deliver: Razorpay adapter (HTTP) behind the provider interface; idempotency backed by DB;
  transactional outbox → SQS + relay; webhook worker (verify, dedupe, out-of-order, DLQ);
  reconciliation worker (backoff, escalate); refund lifecycle (capped, single-per-key).
- Files: `api/modules/payments/*`, `api/modules/webhooks/*`, `api/modules/reconciliation/*`,
  `api/modules/refunds/*`, `api/workers/*`.
- Exit: timeout → UNKNOWN → reconcile → PAID proven with the real DB; no duplicate charge.

## Phase 5 — GROW + Protocol Gateway service
**Goal:** bounded revenue growth and protocol normalization.
- Deliver: campaign service translating the budget guards to repositories (atomic reservation,
  caps, expiry, merchant approval, A/B config); growth agent (LangGraph) proposals;
  protocol gateway live adapters over real transport (MCP/A2A/…).
- Exit: campaign spend never exceeds budget; A/B + incremental measurement; gateway produces
  canonical intents only (never a payment action) against live adapters.

## Phase 6 — Hardening (production readiness)
**Goal:** observability, security, and CI gates for everything.
- Deliver: OpenTelemetry tracing + money-path metrics + alerts; structured logging everywhere;
  red-team/e2e suites; make `integration` + `frontend` + `e2e` **required** CI checks; DR
  drills; Transaction Passport + audit verified end-to-end; docs/ADRs finalized.
- Exit: `docs/36-production-readiness-checklist.md` fully evidenced; red-team green.

## Sequencing rule (why auth first)
AuthN/AuthZ + tenant isolation are the boundary everything else depends on. Building the money
path before a real identity boundary would be unsafe. Each phase keeps the repo green and is
independently demonstrable, so no "big-bang" integration.
