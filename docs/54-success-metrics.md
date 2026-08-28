# 54 — Success Metrics

> Measurable outcomes tied to the three pillars. **Rules:** (1) never invent
> performance numbers without a stated traffic assumption; (2) never fabricate revenue
> predictions (they are labeled estimates); (3) safety metrics are reported as counts
> of *attempts* and *verified* outcomes, not "zero by design" claims.

## 1. Traffic assumption (baseline for latency/loss)

- 100 merchants; 10k AI-buyer sessions/day (peak ~15k/h, ~5 rps sustained, 20 rps burst).
- 3k orders/day (Test Mode), 6k webhook events/day, 10k agent tool calls/day.
- Target: control-plane p95 ≤ 250 ms per API (excluding LLM); LLM tool+tokens budgeted
  separately; policy p95 ≤ 50 ms; risk p95 ≤ 100 ms; payment initiate p95 ≤ 2 s
  (network-bound to provider).

## 2. Merchant Growth (GROW)

| Metric | Definition | Honesty note |
|---|---|---|
| Revenue uplift | (A/B) incremental GMV vs. control | Requires control group; confidence interval, not a single number |
| Conversion uplift | Incremental conversion rate | Same control caveat |
| AOV uplift | Mean order value delta | Baseline-dependent |
| Upsell / cross-sell conversion | % of anchor orders with attached offer | If offer shown then purchased |
| Campaign ROI | (incremental margin − cost) / cost | Explicit coupon cost |
| AI-generated vs AI-assisted vs organic GMV | Attribution split | Conservative: only label AI-generated where the offer was agent-created and accepted |
| Proposal acceptance | % of growth-agent proposals approved | Measures proposal quality, separate from uplift |

## 3. Agent Commerce (SELL)

| Metric | Definition |
|---|---|
| Catalog discovery success | % of buyer queries returning ≥1 relevant product |
| Cart creation success | % of discovery → cart |
| Checkout success | % of cart → authorization request |
| Payment success | % of payment initiations that reach CAPTURED (authoritative) |
| Agent transaction completion | % end-to-end discovery→paid |
| AI buyer to order | % of sessions producing an order |

## 4. Safety (PROTECT) — how we measure "safe"

| Metric | Definition | Target |
|---|---|---|
| Unauthorized financial actions | Financial actions executed with invalid/missing authz | 0 (verified, with detection+blocking proven) |
| Policy bypass attempts | Actions that reached payment without policy ALLOW | 0, plus all attempts logged |
| Duplicate payments | Same idempotency key double-charged | 0 |
| Replay successes | Authz/approval/webhook replayed to a second action | 0 |
| Prompt-injection enforced blocks | Injected agents that were blocked before payment | 100% of injected attempts blocked, logged |
| Cart-tamper rejections | authz invalid because cart changed | 100% + logged |
| Policy/risk denial rate | % of intents denied | Tracked; target = merchent-policy-driven, used as signal |
| Human approval rate | % HIGH/CRITICAL escalated | Tracked; sampling for correctness |

## 5. Operations & Reliability

| Metric | Definition | Target (given §1 assumption) |
|---|---|---|
| API latency | p50/p95/p99 control-plane API | p95 ≤ 250 ms |
| LLM/tool latency | p95 of agent tool + LLM round | measured; budgeted, not mixed with control-plane |
| Payment failure rate | authoritative FAILED / initiated | track, provider-dependent |
| Payment unknown rate | UNKNOWN / initiated | track; low is good, not hidden |
| Reconciliation success | UNKNOWN → resolved / total UNKNOWN | ≥95% auto-resolve; rest manual-escalated |
| Webhook duplicate rate | deduped / received | track; indicator of provider behavior |
| Recovery/restore | restore test pass | quarterly |
| Availability | multi-AZ | ~99.9% (honest, not guaranteed) |

## 6. Success gates for launch

AegisPay is considered production-ready when:
1. **$1.1** Safety: verified 0 unauthorized actions / 0 duplicate charges over a test
   window + red-team suite green (see `docs/38`).
2. **$2.1** Reliability: reconciliation auto-resolves ≥95% of `UNKNOWN`; no blind retry
   anywhere in code (static + test proof).
3. **$3.1** Explainability: 100% of test transactions have a retrievable, verified
   Transaction Passport.
4. **$4.1** Isolation: cross-tenant access tests fail to cross the boundary (RLS + app).
5. **$5.1** Observability: dashboards + alerts exercised in a chaos drill.

These are evidence-based, not aspirational. Targets are recalibrated as Test-Mode data
accumulates; we do not publish speculative SLAs.
