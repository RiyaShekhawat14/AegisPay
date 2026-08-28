# 36 — Production Readiness Checklist

Gate for shipping AegisPay on live credentials (or the challenge final). Each item is
evidence-backed; nothing is "tick by design".

## Security
- [ ] Authentication: OIDC users + MFA; scoped API keys hashed/rotatable; mTLS service
  identity
- [ ] Authorization: RBAC + ABAC; every money path tenant-scoped; agent scopes separate
  from user RBAC
- [ ] Secrets: none in Git/frontend/LLM/log/plaintext DB; Secrets Manager + KMS rotates
- [ ] Encryption: TLS transit; KMS at rest; field-level for PII/sensitive
- [ ] Rate limits: API + per-agent-tool + per-tenant; tested under load
- [ ] Webhook security: signature verify + timestamp window + dedupe + idempotent apply
- [ ] Prompt-injection protection: catalog DATA-only, tool allowlist, typed args,
  deterministic policy, red-team green
- [ ] Agent isolation: no money tool reachable from LLM; no agent self-elevation
- [ ] SSRF/SQLi/CSRF/CORS hardened; WAF; dependency scanning

## Payments
- [ ] Idempotency: unique constraints + replay-returns-prior + request-hash conflict
- [ ] State machine: legal/illegal transitions unit-tested; UNKNOWN exit only via
  webhook/reconcile
- [ ] Webhooks: verified, dedupe, DLQ, out-of-order safe
- [ ] Reconciliation: UNKNOWN→lookup→resolve; no blind retry; escalation path
- [ ] Refund safety: capped to captured; idempotent; policy-gated
- [ ] Failure recovery: circuit breakers + backoff + fail-closed on the money path

## AI
- [ ] Tool allowlist (safe) + typed outputs; dangerous tools not exposed
- [ ] Structured output validator in the runtime
- [ ] Policy enforcement on every proposed action
- [ ] Risk engine separate + non-authoritative LLM
- [ ] Human approval: scoped, expiring, non-replayable, non-stale
- [ ] Evaluations: red-team + refusal/hallucination controls pass in CI

## Trust
- [ ] Policy engine deterministic + versioned + immutable + rollback-able
- [ ] Risk engine explainable (factors + model_version)
- [ ] Transaction Passport: signed, verifiable, evidence per decision
- [ ] Audit ledger: append-only, RLS read-only, hash-chained, S3 anchor, verifier runs
- [ ] Campaign budget ledger: no overspend; A/B + incremental measurement honest

## Reliability
- [ ] Timeouts/retries/circuit breakers on every external dependency
- [ ] Queue + DLQ + outbox (no lost/duplicate events)
- [ ] Backups + PITR; documented RPO ≤15m / RTO ≤1h
- [ ] Multi-AZ; restore drill passed
- [ ] Global emergency kill switch: engages, blocks new payments/refunds/campaign spend
- [ ] Chaos/DR exercised; fail-closed behavior verified

## Observability
- [ ] Metrics: money funnel, decision path, webhooks, reconciliation, growth
- [ ] Logs: correlation/tenant/transaction IDs; no secrets/PII
- [ ] Tracing: full financial span chain
- [ ] Alerts: money-path, security, DLQ, reconciliation-stuck, budget/margin
- [ ] Dashboards: money health, decision health, protection, growth

## Compliance / data
- [ ] PII minimization + field encryption + redaction (logs/events)
- [ ] Retention + deletion jobs with audit log
- [ ] Access controls (RLS + RBAC) proven by isolation tests
- [ ] Auditability: every financial decision explainable; legal review flagged

## Product (challenge)
- [ ] Merchant onboarding (Razorpay Test Mode) + AI-readable catalog
- [ ] AI buyer discovery→checkout→payment→resolution
- [ ] Growth agent + campaign with approval + budget/margin caps
- [ ] Analytics (GMV, uplift, ctrl group) + honest attribution
- [ ] At least one failure shown & handled (UNKNOWN→reconcile)

## Evidence gates
- [ ] Red-team suite green (no unauthorized $, no duplicate charge, no replay, no
  cross-tenant, no PII leak)
- [ ] Isolation test: cross-tenant access blocked
- [ ] Restore drill passed (measured RTO)
- [ ] Load test meets p95 targets under the stated traffic assumption
- [ ] 100% test transactions have a verified Transaction Passport
