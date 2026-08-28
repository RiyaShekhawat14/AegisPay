# 25 — Load Testing

## 1. Traffic assumption (explicit; do not invent beyond this)

- 100 merchants; 10,000 AI-buyer sessions/day; 15,000 peak-hour max (≈5 rps
  sustained, ~20 rps burst).
- 3,000 orders/day (Test Mode); 6,000 webhook events/day; 12,000 agent tool calls/day.

**Targets (given the above):**
- Control-plane API p95 ≤ 250 ms; p99 ≤ 500 ms (excluding LLM).
- Policy p95 ≤ 50 ms; risk p95 ≤ 100 ms (rule+stat; ML optional/cached).
- Payment initiate p95 ≤ 2 s (network-bound to provider).
- Reconciliation: 95%+ auto-resolve.
- Queue drain: no backlog growth at 2× the baseline burst rate for 30 minutes.

## 2. Load model & profile

- **Burst:** 20 rps on the money path for 5 min; 100 rps on read/catalog for 5 min.
- **Sustained:** 5 rps money path for a steady window.
- **Webhook storm:** 200/hr duplicate + 100/hr new, verifying dedupe + ordering.
- **Agent tool spam:** hammer catalog + cart tools; assert rate/action budgets hold.

## 3. Scenarios (k6)

1. **Buyer journey:** discover → cart → authorize → pay (Test Mode) → resolve.
2. **Catalog read** scale.
3. **Webhook ingest** scale + dedupe.
4. **Agent tool** throughput + budget enforcement.
5. **Reconciliation** worker throughput under UNKNOWN storm.

## 4. Failure/limit targets

- Rate limit must not leak cross-tenant, must not bypass policy.
- Redis/DB saturation marks a boundary; at saturation the control plane **fails
  closed** (rejects money actions), which is acceptable and tested.
- No duplicate payments under load (idempotency holds).

## 5. Tooling

k6 for HTTP/API; a pytest/asyncio load harness for webhook/worker; run against staging with
Razorpay Test Mode. Capture latency percentiles, throughput, error rates, DB/Redis
saturation.

## 6. Interpret, don't fabricate

We publish the numbers **with the traffic assumption**. We do not claim an "industry-
leading 99.99%" or a specific p99 without this measurement. Targets are recalibrated
as real Test-Mode volume appears.
