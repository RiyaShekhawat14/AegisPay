# 24 — Testing Strategy

## 1. Pyramid

| Level | Scope | Tools | Gate |
|---|---|---|---|
| Unit | policy DSL, risk score/fusion, state machines, authorization, idempotency, provider adapter mocks | pytest, unittest | every PR |
| Integration | PostgreSQL (RLS), Redis, SQS, Razorpay Test Mode real calls | testcontainers + real Test Mode | every PR (or nightly) |
| E2E | complete purchase flow (discover → authorize → pay → webhook → reconcile → passport) | pytest harness | staging, before deploy |
| Security/Red-team | the `docs/38` suite | harness | mandatory gate |
| Failure | $4.2 scenarios | chaos harness | staging |
| Load | realistic traffic | k6 | pre-production |

## 2. Unit (highest value)

- **Policy engine:** table-driven `(facts → decision)` covering precedence, DENY-wins,
  fail-closed, hour/category/limit, versioning/rollback. Mutation coverage high.
- **Risk engine:** score/level thresholds, factor weighting, clamping (LOW can't
  override DENY), LLM-note isolation, model_version.
- **State machines:** legal/illegal transition sets; terminal-state immutability;
  UNKNOWN exitable only via webhook/reconcile.
- **Authorization:** binding, expiry, single-use, cart-hash invalidation, replay
  rejection.
- **Idempotency:** same-key replay returns prior result; different request under same
  key → conflict; TTL.
- **Provider adapter:** mocked Razorpay to verify the canonical mapping + that no
  provider concept leaks.

## 3. Integration

- Real PostgreSQL with RLS: cross-tenant read returns empty; audit is read-only;
  unique constraints fire (idempotency, single approval, refund cap).
- Redis: lock sanity, rate limiting, cache invalidation; Redis down → fail-closed.
- **Razorpay Test Mode**: create order, initiate payment, capture, refund, webhook
  signature — against real Test APIs (no mock for money-semantics tests).

## 4. E2E

Full purchase journey with a real (test-mode) order: agent discovers → cart →
authorization → policy/risk → auto-approve or human approval → payment → capture →
webhook → reconcile (if UNKNOWN) → passport + audit. Assert the exact state sequence.

## 5. Failure testing

| Fault | Expected | Assert |
|---|---|---|
| Provider timeout | UNKNOWN; no retry | payment stays UNKNOWN; no second charge |
| Duplicate webhook | dedupe no-op | single state application |
| Delayed webhook | reconcile after grace | resolved via reconcile |
| Out-of-order webhook | no regression | state stays terminal |
| Provider outage | fail-closed/unknown | no payment initiated |
| DB failure | reject money actions | no unwritten state |
| Redis failure | degrade gracefully | no false writes |
| Queue failure | outbox + DLQ | events eventually processed / isolated |
| LLM failure | agent path degrades | control plane still processes webhooks/reconcile |
| Policy/risk unavailable | fail-closed | deny/escalate, not allow |

## 6. Security tests

From `docs/38`; plus auth (missing/invalid scope), RBAC (role can't do more), RLS
(isolation), replay, provider-side tampering (fake webhook), and a check that no LLM
tool can reach a money tool.

## 7. Conformance

- Assert `Invariant 1`: no code path from the agent/LLM layer to a money tool.
- Assert `Invariant 5`/`7`: cart change and approval reuse are rejected.

## 8. Test environment

Testcontainers for Postgres/Redis/localstack; Razorpay Test Mode; deterministic seeds.
CI runs the safety-critical set; staging runs E2E + red-team every deploy.

## 9. Non-goals

We don't fake "LLM behavior" for the safety tests — we drive the actual control-plane
outcome and assert invariants, since correctness must not depend on model behavior.
