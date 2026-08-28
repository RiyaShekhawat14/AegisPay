# 28 — Merchant Growth Agent

> GROW pillar. The growth agent increases merchant revenue with AI (upsell, cross-sell,
> bundles, campaigns, segmentation, re-engagement, personalization). It proposes and
> measures; it does **not** control money. Every financial effect flows through the
> PROTECT pipeline (policy → risk → approval → audit).

## 1. Responsibilities

- Mine merchant transaction data (test-mode orders) for affinity and opportunity.
- Propose explainable revenue actions: cross-sell, upsell, bundles, campaigns.
- Segment customers; plan re-engagement.
- Produce honest, labeled estimates (never fabricated revenue).
- Measure results; feed back into the model (bounded, no self-elevation).

## 2. Boundaries (the important part)

The growth agent is a **proposal layer**. It may:
- read merchant purchase/affinity data;
- propose a campaign with a discount and a budget;
- recommend a cross-sell to an AI buyer.

It may **not**:
- change prices without a policy-approved campaign;
- create an uncapped budget;
- directly order a refund/discount that violates margin policy;
- access customer PII beyond what segmentation needs (minimized);
- self-approve its own campaign.

## 3. Output contract — explainable opportunity

```jsonc
{
  "opportunity_id": "opp_...",
  "kind": "cross_sell",
  "anchor_product": "prod_999",
  "target_products": ["prod_1000", "prod_1001"],
  "affinity": 0.34,                     // measured, not implied
  "confidence": 0.81,
  "estimated_uplift": { "low": 0.03, "mid": 0.08, "high": 0.14 },  // range, labeled estimate
  "recommended_action": { "type": "percent_discount", "value": 10, "budget_minor": 500000 },
  "reason": "34% of buyers of Running Shoes purchased Running Socks in the trailing 90d.",
  "evidence": ["order_1","order_5","order_9"],
  "estimates_are": true,                // explicit honesty flag — regenerated each run
  "data_window": "last 90 days",
  "model_version": "affinity-v3"
}
```

**Honesty rule:** `estimated_uplift` is a labeled range derived from observed
historical correlation, clearly marked as an estimate, regenerated from fresh data on
each run. AegisPay never presents a plausible-looking but speculative number as fact.

## 4. Proposed decision path → PROTECT

```
Opportunity (growth agent, T1)
   ↓
Campaign Proposal (typed)
   ↓
Campaign Policy Engine            ← deterministic: max discount, max budget, min margin,
   ↓                                max duration, customer frequency limits
Risk Engine                       ← score the campaign (budget risk, targeting risk)
   ↓
Merchant Approval (HITL)          ← campaigns need merchant opt-in (see §5)
   ↓
Campaign Execution (bounded)      ← only within approved budget/discount/margin
   ↓
Measurement + Audit               ← revenue impact + full trail
```

This is the same pipeline as a sale; the growth agent is just a different *proposer*.
It never has a path that bypasses policy.

## 5. Human-approval policy for campaigns (sensible defaults)

- **Campaigns always require merchant approval** (autonomy dial decides whether
  execution is manual or auto after approval; see `docs/30`).
- Discount cap, budget cap, margin floor, duration cap, and per-customer frequency are
  deterministic rules, not model judgment.
- Any proposal violating a rule is `DENIED` and the reason is recorded.

## 6. Safeguards against abuse

| Risk | Mitigation |
|---|---|
| Excessive discount | Policy `max_discount_pct`, margin floor; computed against merchant margin, not list price |
| Budget overspending | Budget cap + hard-stop when `spent>=budget`; idempotent execution |
| Margin destruction | Minimum-margin rule; cross-sell approved only if margin-positive |
| Spam | Per-customer frequency cap + suppression list |
| Discriminatory targeting | Only value/behavior segmentation allowed; no protected-class attributes as inputs |
| Customer manipulation | No aggressive urgency; no fabricated scarcity; all offers labeled |

## 7. Attribution

Growth outcomes are split **AI-generated** (agent proposed the exact offer/bundle),
**AI-assisted** (agent informed a human decision), and **organic**. Attribution is
explicit and conservative to avoid misleading the merchant (see `docs/54`).

## 7b. Budget ledger

Every campaign has a **budget** and a **spent counter**. Each discount/offer costs
against it in an atomic update (`spent + cost <= budget`), so it can never overspend.
The moment the envelope is used up, the campaign **pauses itself** and emits a
`campaign.budget.exceeded` event. The AI cannot raise the budget — only a merchant/policy
admin can, and that change is audited.

## 7c. A/B testing + incremental revenue

Growth is measured **honestly, not claimed**:
- A **control group** does not get the offer; a **test group** does.
- **Incremental revenue = test − control**, so we isolate the real effect from seasonality
  and baseline.
- Uplift is reported as a **range** and explicitly labelled an estimate; we never reuse a
  lucky number as a promise.
- The AI is only repeated if the measured effect is real and positive — otherwise it
  learns and stops.

## 8. Observability

Campaign conversion, revenue uplift, discount cost, margin impact, approval rate,
budget utilization, opportunity-quality precision/recall. Alerts on budget breach,
margin breach, and any proposed action that would have been denied (near-miss
signals for prompt-injection/tool-poisoning detection).

## 9. Security

Treat the growth agent like any agent: identity + scopes + tool allowlist + rate
limits + audit. Its data access is scoped to *aggregate* affinity/segment data, with
PII minimized. It cannot modify policies, budgets, or its own trust level.
