# 29 — Campaign Orchestrator

> GROW pillar. Orchestrates a revenue campaign end-to-end, bounded by deterministic
> financial rules. A campaign is a *sell-side offer* (not an order), but every
> budgetary/economic aspect is still a financial decision and is gated.

## 1. Pipeline

```
Opportunity
   ↓
Campaign Proposal (typed: offer, discount, budget, targeting, duration)
   ↓
Campaign Policy Validation     ← deterministic caps (discount, budget, margin, duration, frequency)
   ↓
Risk Score                    ← budget risk, targeting quality, velocity
   ↓
Merchant Approval (HITL)      ← unless autonomy level auto-approves within caps (L≥2)
   ↓
Execution (bounded, idempotent)
   ↓
Measurement (revenue, uplift, margin, cost)
```

## 2. Deterministic campaign rules (the DSL)

| Rule | Default | Bound |
|---|---|---|
| Max discount % | 10% | Hard cap (`max_discount_pct`) |
| Campaign budget | merchant-set | Hard cap (`budget_minor`); execution stops at `spent>=budget` |
| Min margin | e.g. 18% | `min_margin_pct`; proposal rejected if margin-negative post-discount |
| Max duration | 30 days | `max_duration_days` |
| Per-customer frequency | 1 | `max_actions_per_customer` |
| Target segment | value/behavior only | no protected-class attributes |

These are deterministic and versioned; the merchant (policy_admin) can adjust the caps,
and every change is audited. **The LLM cannot change them.**

## 3. Campaign aggregate state

```
DRAFT → PROPOSED → VALIDATED → PENDING_APPROVAL → APPROVED → ACTIVE
   │        │           │            │                │
   │        │           │            └──> REJECTED    ├──> PAUSED
   │        │           └──> VALIDATION_FAILED        └──> COMPLETED
   │        ├──> WITHDRAWN
   └──> ARCHIVED
```

`ACTIVE → PAUSED → ACTIVE` allowed (merchant/ops). Terminal: `COMPLETED`,
`ARCHIVED`, `REJECTED`. Budget exhaustion auto-pauses (`budget.exceeded` event).

## 4. Execution — safe & idempotent

- **Actuators:** the only things a campaign can do are (a) attach an approved discount
  to a product/order, (b) recommend an item, (c) emit an offer. None of these move
  money directly; they influence *subsequent* orders, which still go through the
  normal order→payment pipeline.
- **Idempotency:** campaign execution is keyed by `(campaign_id, action_reference)` so
  re-delivery of a recommendation or a retried actuator is a no-op.
- **Budget guard is atomic:** `spent` is updated with `spent + cost <= budget` in a
  transaction / `SELECT ... FOR UPDATE`. On breach, execute nothing and emit
  `campaign.budget.exceeded`.

## 5. Merchant autonomy integration

The autonomy level (L0–L4, `docs/30`) decides whether `PENDING_APPROVAL` is automatic
(L2+) or requires a human (L0–L1 for execution-after-proposal). Even at L4, the
deterministic caps still bind — autonomy never overrides minimum margin or max budget.
This is the key nuance: **autonomy raises who can approve, never what may be approved.**

## 6. Guardrail summary

- No campaign can exist without a merchant-approved budget and discount.
- No discount can drop margin below the floor.
- No more than `max_actions_per_customer` per customer; suppression honored.
- No targeting on protected classes.
- Every campaign action is audited and attributable to the campaign and the agent.

## 7. Observability

Budget utilization %, margin after discount, conversion uplift vs. control, ROI,
discount leakage. Alerts: budget breach, margin breach, abnormal spend velocity,
unexpected high-frequency segments.

## 7b. A/B testing + incremental measurement

- A campaign enters a **test group**; a matched **control group** receives no offer.
- **Incremental revenue = test − control**, so we measure the real lift, not the raw
  sales the campaign happened to run next to.
- Results are reported as a **range** with a confidence level and labelled an estimate.
- On a positive, replicable result the campaign graduates to wider roll-out; on a null
  or negative result it is paused and the agent is tuned. The AI only scales what it
  proves works.

## 7c. Kill switch integration

A campaign is always subject to the global **emergency kill switch**. When engaged, no
new campaign discount can be applied and pending campaign spend is halted, while
reconciliation and audit remain active. The switch is high-privilege, audited, and
requires a human + a second role.

## 8. Failure behavior

- Rule violation → proposal `DENIED` with reason (no campaign created).
- Budget breach mid-run → campaign pauses; overspend prevented atomically.
- Merchant does not approve in time → proposal `EXPIRED`.
- Actuator error → retry with backoff; idempotent (no double-apply, no double-discount).
