# AegisPay — Production Readiness

> Final gate for AegisPay. This is the checklist to ship — not a feature, but the confidence
> set: everything documented, verified, and safe to run.

## 1. Run it locally

```bash
# one command boots the stack (Postgres + API + AI runtime)
make dev

# verify everything is green (lint + type + tests)
make verify

# run tests against a real DB
cd api && pip install -e ".[dev]"
DATABASE_URL=postgresql+asyncpg://aegispay_app:aegispay@localhost:5433/aegispay \
  python -m pytest -q tests/unit tests/integration tests/redteam
```

## 2. Required environment (secrets must be set in prod, never baked in)

Copy `api/.env.example` → `api/.env` and set:

| Var | Prod value |
|---|---|
| `DATABASE_URL` | app role (never superuser; RLS enforced) |
| `JWT_SECRET` | strong, generated secret |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Razorpay test/live keys (server-side only) |
| `RAZORPAY_WEBHOOK_SECRET` | **must be set** — without it the webhook verify falls back to a mock |
| `CONTROL_PLANE_URL` / `CONTROL_PLANE_TOKEN` | AI runtime → control plane (isolated) |
| `FIELD_ENC_KEY` | envelope key for sensitive fields |

The AI runtime image must **not** receive `DATABASE_URL`, Razorpay secrets, or money tools.

## 3. Security invariants (verified by the red-team suite)

- No LLM ever reaches a money path; the AI runtime has no DB/secrets/money tools.
- Every financial action passes policy → risk → authorization (see `authorizations`).
- Unknown payment state is never blindly retried — reconcile (`reconciliation/run`).
- Every payment is idempotent; cart changes invalidate authorization.
- Cross-tenant reads/writes are blocked by RLS (app role has no `BYPASSRLS`).
- Audit events are append-only + hash-chained (tamper-evident).

Run the adversarial suite to confirm none of these regress:
```bash
python -m pytest -q tests/redteam
```

## 4. Observability

- `GET /v1/health` — liveness
- `GET /v1/readyz` — DB readiness (503 when unreachable)
- `GET /v1/live` — liveness
- `GET /v1/metrics` — Prometheus text (request/status + payment counters)
- Structured JSON logs carry `request_id` + `tenant_id`; OTel spans wrap each request (set
  `OTEL_EXPORTER_OTLP_ENDPOINT`).

## 5. Demo flow (one command, test mode)

Buyer: `/login` as **Buyer** → `/shop` add to cart → `/shop/cart` → authorize & pay.
Merchant: `/login` as **Merchant** → dashboard → catalog → opportunities → campaigns.
Control plane: `make dev`; AI runtime on `:8001`; API on `:8000`.

## 6. Not built yet (explicit, honest)

- Production Razorpay live keys / real money movement (test mode now).
- NPCI / UPI production integration (interface/readiness only).
- K8s / AWS / Terraform (compose is enough); SQS/Redis wiring (outbox table + in-memory now).
- A real user/password login endpoint (auth is token-based; the UI login is a session gate).
- Playwright UI smoke (needs the compose-orchestrated stack running).

## 7. Definition of Done

- [x] Backend starts + DB + health probes
- [x] Merchant/catalog + auth + tenant isolation
- [x] Cart + policy + authorization
- [x] Razorpay (test-mode) payment path
- [x] Webhooks + reconciliation + audit + passport
- [x] AI buyer + merchant (GROW/SELL) UI
- [x] Protocol gateway + workers + red-team + E2E + observability
