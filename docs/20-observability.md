# 20 — Observability

## 1. Pillars

OpenTelemetry instrumentation + CloudWatch (metrics/logs) + a trace backend. All three
bind via shared IDs: `request_id`, `trace_id`, and the business `tenant_id`,
`agent_id`, `transaction_id`.

## 2. Metrics

### Payments
`payment_initiated_total`, `payment_succeeded_total`, `payment_failed_total`,
`payment_unknown_rate`, `payment_capture_latency`, `payment_refund_total`,
`reconciliation_success_rate`, `reconciliation_unknown_total`.

### Decision path
`policy_evaluation_latency`, `policy_denial_rate`, `risk_evaluation_latency`,
`risk_escalation_rate`, `authorization_issued_total`, `authorization_denied_total`,
`approval_required_rate`, `approval_rate`, `step_up_rate`.

### Agents
`agent_tool_calls_total`, `agent_tool_failure_rate`, `agent_latency`,
`agent_action_rate`, `agent_rejected_rate` (policy denied / budget exceeded).

### Webhooks
`webhook_received_total` by provider, `webhook_verified_total`, `webhook_deduped_total`
(duplicate rate), `webhook_signature_failure_total`, `webhook_processor_latency`,
`webhook_dlq_depth`.

### Growth / campaigns
`campaign_created_total`, `campaign_conversion`, `campaign_budget_utilization`,
`campaign_margin_impact`, `revenue_uplift`.

### Platform
`request_latency` (p50/p95/p99), `db_pool_wait`, `queue_depth`, `circuitbreaker_open`.

## 3. Logs

- Structured JSON; always include `request_id, trace_id, tenant_id, agent_id,
  transaction_id` where available.
- **Never** log: Razorpay secrets, card/PAN, provider secrets, tokens, raw PII. Redaction.
- Levels: `INFO` for business events, `WARN` for odd-but-handled, `ERROR` + stack for
  failures, `DEBUG` for the development path then dropped in prod.
- Correlation: a single logical journey uses the same `correlation_id`; causality via
  `causation_id`.

## 4. Tracing

Trace the full financial path:
```
User → Agent → Tool → Policy → Risk → Authorization → Payment → Razorpay → Webhook → Reconciliation
```
- Instrument the provider adapter (outbound spans), policy/risk/authorization, and the
  webhook processor.
- Parent-child relationships let an SRE see exactly which link is slow/failing.
- Sampling: 100% of money-path traces (they're low-volume, high-value); sampled on bulk.

## 5. Alerts

- Money-path: payment success/failure/unknown alarms, unusual rate, UNKNOWN-stuck
  reconciliation (not resolving), duplicate-payment detector, refund-scope violation.
- Security: signature failures, authz-denial spikes, injection-detection hits,
  privilege-escalation attempts, cross-tenant attempts.
- Reliability: DLQ depth, circuit-breaker open, DB/Redis/queue saturation, policy/risk
  engine outage (fail-closed actions).
- Growth: budget/margin breach, approval queue risk/unresolved approvals.

## 6. Dashboards

- Money health: payment funnel, unknown/reconcile, idempotency, webhook pipeline.
- Decision health: policy/risk/approval.
- Growth: GMV, AI-generated vs assisted vs organic, campaign ROI.
- SLO/service: latency, errors, saturation, resource; plus a "protection" dashboard
  proving red-team green + invariants.

## 7. SRE practice

- SLIs/SLOs: availability (honest), latency p95, reconciliation auto-resolve rate,
  webhook processing lag.
- Error budget + burn alerts; on-call runbook (`docs/43-runbook`).
