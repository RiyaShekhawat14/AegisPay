# 40 — Engineering Roadmap

## Phase 0 — Foundations (weeks 0–4)
- FastAPI modular monolith skeleton (control-plane + ai-runtime), CI/CD scaffold (lint/test/build).
- PostgreSQL with RLS multitenancy + migrations.
- Secrets layer; tenant context; standard error envelope.
- **Exit:** green dev harness; tenant isolation test passes.

## Phase 1 — Test-mode commerce core (weeks 4–9)
- Razorpay adapter (createOrder/initiate/capture/refund/fetch) in Test Mode.
- Catalog import → canonical model; cart aggregate (server price, cart_hash).
- Idempotency guard; payment state machine; order aggregate.
- **Exit:** a payment can be authorized & captured; idempotency proven (replay returns
  prior), provider timeout tested.

## Phase 2 — Webhooks + reconciliation (weeks 8–12)
- Webhook gateway (signature/timestamp/dedupe/raw persist) + processor + DLQ.
- UNKNOWN handling + reconciliation worker + escalation.
- **Exit:** duplicate/out-of-order/delayed webhooks handled; UNKNOWN→reconcile→resolve
  without double-charge.

## Phase 3 — Trust: policy/risk/authz/HITL (weeks 11–17)
- Deterministic policy engine + DSL + versioning/rollback + deny precedence.
- Explanable risk engine (rules+stat+optional ML; LLM non-authoritative).
- Transaction-bounded authorization + human approval (scoped/expiring/non-replayable).
- **Exit:** policy/risk/authz tests + HITL flow; RED-TEAM core scenarios green.

## Phase 4 — Audit + Transaction Passport (weeks 15–19)
- Append-only hash-chained audit ledger + S3 anchor + verifier.
- Transaction Passport generation + verification + UI.
- **Exit:** any test transaction yields a verified passport + integrity check.

## Phase 5 — Agent/protocol layer (weeks 18–24)
- Safe tool definitions; strict typed schemas; action budgets; rate limits.
- MCP server + A2A endpoint over the canonical model; protocol gateway.
- Catalog DATA-vs-INSTRUCTIONS separation + injection classifier.
- **Exit:** an agent (MCP/A2A) completes a purchase through the full PROTECT path;
  no LLM path reaches a money tool.

## Phase 6 — GROW: growth agent + campaigns (weeks 22–28)
- Growth agent (affinity, cross-sell, upsell, bundles) + explainable opportunity output.
- Campaign orchestrator with budget/margin/discount/frequency caps + approval.
- Analytics with honest attribution (AI-generated/assisted/organic).
- **Exit:** campaign proposed → policy → approval → executed → measured within caps.

## Phase 7 — Hardening (ongoing, pre-production)
- Observability (metrics/logs/traces/alerts/dashboards).
- Red-team + security + chaos + load + DR drills.
- Secrets/encryption/key rotation; dependency scanning; images signed/scanned.
- **Exit:** `docs/36` production-readiness checklist fully evidenced.

## Phase 8 — Production (post-gate)
- Live credentials go-live behind the full gate (still bounded, human-approval bias at
  first); roll-out of higher autonomy levels incrementally after proving oversight.

## Priority note
Correctness/safety (Phases 3–4) are not deferred: they land **with** the first money
path (Phases 1–2), because shipping payment without deterministic policy/audit would
violate the core invariant. GROW (Phase 6) is sequenced after PROTECT is solid, since a
growth agent without a safe money path is not shippable.

## Rate/sequencing trade-off
We sequence security-first to avoid "build fast then retrofit safety" — retrofitting
deterministic authz onto an ad-hoc payment path is where fintechs get hurt. The
roadmap optimizes for correctness and safety, then revenue, keeping developer velocity
via the modular monolith.
