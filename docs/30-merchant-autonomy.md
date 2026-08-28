# 30 — Merchant Autonomy Levels

Autonomy is a **per-merchant (and optionally per-agent) dial** that controls how much
an AI agent may *propose and auto-execute*. It never controls what the deterministic
control plane may *authorize*. This is the crux: **autonomy changes who may approve,
not what may be approved.**

## 1. The levels

| Level | Name | Agent may do | Human involvement | Capability |
|---|---|---|---|---|
| **L0** | Observe | Read catalogs, run analyses, produce reports | Always | Analytics + recommendations, no execution |
| **L1** | Recommend | Propose actions (recommend, cross-sell, campaign idea) | Every financial action | Human decides; agent advises |
| **L2** | Auto-execute low-risk | Auto-execute actions within strict caps | Escalation only above caps | Low-risk carts, bounded upsell |
| **L3** | Delegated autonomy | Auto-execute within approved broader caps; request approval for outliers | Approval for exceptions | Routine commerce autonomous |
| **L4** | Highly autonomous | Auto-execute within maximum caps; broader mandate | Oversight/audit, step-up for critical | Max safe throughput, never unrestricted |

## 2. What is invariant across all levels

Regardless of level:
- All actions pass **policy → risk → authorization**.
- **Deterministic caps** (max transaction, per-txn, daily, category, hours) always bind.
- **Minimum-margin** (growth) and **max-budget** (campaigns) always bind.
- **Human approval** is required above the level's threshold (a L3 merchant with a
  ₹8,999 high-risk transaction still needs approval if it exceeds the L3 cap).
- Agents **cannot** change their own level or policy.
- Every action is audited and idempotent.

## 3. What each level actually permits (concrete)

### L0 — Observe
- `search_catalog`, `get_product`, `compare_products`, analytics.
- No cart that leads to a request for payment authorization without explicit human
  action. Provides dashboards and reports.

### L1 — Recommend
- Everything in L0, plus `create_cart`/`add_to_cart` and `request_checkout` — but the
  resulting authorization request is **always** queued for a human approve/reject.
- No payment action auto-executes.

### L2 — Auto-execute low-risk
- L1 + `request_authorization`; low-risk (policy+risk LOW) intents auto-approve and
  auto-execute **within strict caps** (e.g., per-txn ≤ merchant cap, category
  allowed, hours allowed).
- Anything above caps or any MEDIUM/HIGH risk → human or step-up.

### L3 — Delegated autonomy
- L2 + broader caps the merchant explicitly delegates (e.g., up to ₹5,000 auto).
- Outliers above delegated caps and HIGH/CRITICAL risk → human.

### L4 — Highly autonomous
- L3 + maximum caps set by the merchant; step-up auth for CRITICAL risk; continuous
  oversight, audits, sampling, and route-to-human when confidence drops.
- Never fully unrestricted: the deterministic policy and risk engines still gate every
  action; there is no "L5: AI decides everything" because that would violate the core
  invariant.

## 4. How the level is enforced

- Stored on `merchants.default_autonomy_level` and optionally overridden per `agent`.
- The **policy engine** evaluates the effective level for the (merchant, agent) pair
  and applies the corresponding caps and human-approval thresholds.
- Lowering a merchant level is instant (fail-closed, safe). Raising is audited and
  may require a human `policy_admin`.
- A level change is itself an audited event and cannot be performed by an agent.

## 5. Trade-off and honesty

Autonomy is a **risk/utility dial**, not a magic permission. High levels bring more
revenue (GROW/SELL throughput) at more risk of error. AegisPay's answer is: the money
path never loosens regardless of level — mitigations (policy caps, risk, approval,
audit, reconciliation) remain identical at L4; only *the volume and velocity of what
is proposed+executed* increases, bounded by caps. We explicitly document that there is
no fully autonomous money level, because no merchant or regulator should accept one.

## 6. Recommended defaults for the demo

- Onboarding: **L1** (safe, shows the human-approval path).
- A merchant can be bumped to **L2** to show an autonomous low-risk purchase.
- The ₹8,999 HIGH-risk example is above any L2/L3 cap, so it still requires human
  approval — demonstrating that autonomy never overrides safety.
