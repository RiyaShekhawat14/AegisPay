# 50 — Backend Build Plan (continuous, reviewable chain)

One chunk at a time. Each chunk (1) is a single PR, (2) leaves CI green, (3) has a review
focus, and (4) is a **gate** — don't start the next chunk until this one is merged and its
tests pass. This is a dependency chain, not a parallel list.

```
Chunk 1 Foundation & identity  →  2 Data layer  →  3 Commerce execution (cart→order)
   →  4 Authorization + payment  →  5 Webhooks + reconciliation  →  6 Refunds
   →  7 GROW (campaigns)  →  8 Protocol gateway (live)  →  9 Passport/audit + e2e gate
```

## What exists already (start state)
`api/` has: auth (JWT/API-key → Principal; RBAC + agent ABAC), request-id/tenant/rate
middleware, error model, structured logging, observability (OTel), SQLAlchemy session +
models + repositories (tenant-scoped, transactional, atomic budget), Razorpay provider +
mock, and the tested pure logic (policy engine, payment state machine, protocol gateway,
idempotency, cart guards, budget, refund guard, purchase flow). 40 unit tests pass; CI green.
Missing: cart/order/payment **endpoints → services → repos**, webhook/reconciliation **workers
wired to queue**, refund endpoint, GROW endpoints, live protocol transport, e2e/red-team gate.

---

## Chunk 1 — Foundation & identity (mostly done → verify + finalize)
- Deliverables: confirm auth, RBAC/ABAC, middleware, error model, logging/observability,
  `db/session` tenant-pinned session + `get_session` dependency.
- WHY first: everything else requires an authenticated, tenant-bound principal and a
  tenant-pinned DB session.
- Review focus: is tenant derived only from auth? Can an agent reach `payment.execute`?
- Gate: `pytest tests/unit` green + `/v1/me` returns the principal.

## Chunk 2 — Data layer (done → wire into services)
- Deliverables: `db/{session,models,repositories}.py` used by a real service; `DbSession`
  dependency.
- Review focus: RLS is the boundary, not app checks; transactions around money.
- Gate: a repository test proves A cannot read B's rows (integration, Postgres).

## Chunk 3 — Commerce execution (cart → order)
- Deliverables: `services/cart.py` + `services/orders.py` + `routers/carts.py`,
  `routers/orders.py`. Server-owned prices, cart hash + price version, inventory
  reservation + expiry, create order (idempotent) from a locked cart.
- WHY now: produces the order that everything downstream (authorize/pay) depends on.
- Review focus: is any amount/price client-supplied? Does cart change invalidate?
- Gate: create-cart → add-item → lock → create-order persists; e2e green.

## Chunk 4 — Authorization + payment initiation
- Deliverables: `services/authorization.py`, `routers/payments.py` → issue
  transaction-bound, expiring, single-use authorization; initiate payment via `PurchaseFlow`
  (repos + Razorpay + outbox + idempotency); provider timeout → `UNKNOWN`.
- Review focus: authorization bound to cart_hash/amount/version; no blind retry of UNKNOWN.
- Gate: authorize → pay → UNKNOWN on timeout → (test) ; duplicate key = same result.

## Chunk 5 — Webhooks + reconciliation
- Deliverables: wire `workers/webhook_processor.py` (verify, dedupe by provider_event_id,
  out-of-order → idempotent state, DLQ), `workers/reconciliation.py` (backoff, escalate),
  outbox relay → SQS. `routers/webhooks.py` + `services/webhooks.py`.
- Review focus: signature + timestamp first; duplicate = safe no-op; UNKNOWN resolved by
  provider truth only.
- Gate: duplicate/out-of-order webhook + timeout→UNKNOWN→reconcile→PAID proven.

## Chunk 6 — Refunds
- Deliverables: `services/refunds.py` + `routers/refunds.py`: policy + authorization gate,
  capped to captured, single effective per key, AI cannot issue, verified webhook → REFUNDED.
- Review focus: amounts cap; no AI unrestricted refund.
- Gate: refund path + duplicate/over-capture rejected.

## Chunk 7 — GROW (opportunities + campaigns)
- Deliverables: `services/opportunities.py`, `services/campaigns.py`,
  `routers/campaigns.py` (+ `graph/` growth agent). Atomic budget reserve, discount/margin/
  duration caps, merchant approval, A/B config, incremental measurement.
- Review focus: budget never exceeded (row-locked); AI cannot raise its own budget.
- Gate: campaign spend stops at budget; A/B measurement.

## Chunk 8 — Protocol Gateway (live transport)
- Deliverables: `services/gateway.py` over real MCP/A2A/… transport; `dependencies` auth per
  protocol; `websockets/session.py`. Gateway → canonical intent → control plane.
- Review focus: no adapter can yield a money action; identity mapped to canonical agent_id.
- Gate: an MCP/A2A request normalizes to a non-money intent and is rejected at money boundary.

## Chunk 9 — Transaction Passport + audit + production gate
- Deliverables: `services/passport.py` (generated from order+items+authz+policy+approval+
  payment+audit), turn on integration/e2e/red-team as **required** checks, DR docs.
- Review focus: passport verifiable; tamper-evident audit; production checklist evidenced.
- Gate: `docs/36-production-readiness-checklist.md` fully green; red-team green.

---

## How to run the chain (per chunk)
1. Branch from `main` (e.g., `feat/chunk-3-cart-order`).
2. Implement the chunk's services + routers + tests.
3. `make lint type test` → all green, plus any new unit/integration tests.
4. Open a PR; leave it for a peer review; only merge after the review + CI pass.
5. Start the next chunk.

Doing it this way keeps every PR small, reviewable, and leaves the repo always green and
always runnable — no big-bang integration.
