# 10 — Policy Engine

## 1. Purpose

The policy engine is the **deterministic gate** that turns a validated intent into a
decision: `ALLOW | DENY | HUMAN_APPROVAL_REQUIRED | STEP_UP_AUTHENTICATION`. It is
evaluated over **facts**, not probability. The LLM cannot author, edit, or approve
policy; it can only produce an intent that the engine evaluates.

## 2. Why deterministic & versioned

- **Deterministic:** same inputs → same decision. No model nondeterminism on money.
- **Versioned/immutable:** a published policy is immutable; a new version supersedes;
  rollback is a pointer move. Every evaluation records `policy_version`, so you can
  always reconstruct why a decision was made.
- **Auditable:** evaluation inputs and outputs are logged.

## 3. Policy DSL (typed, restricted)

```
policy policy_v12 {
  merchant: ABC-Store
  agent: shopping-agent
  per_txn_limit: 3000           // INR, minor units
  daily_limit:    10000
  categories:      [food, grocery, household]
  blocked:         [alcohol, tobacco]
  human_approval_above:  2000
  step_up_above:         50000
  allowed_hours:   08:00-22:00
  requires:        [valid_mandate, cart_hash_valid]
}
```

Rules are compiled to a typed AST and evaluated in **precedence order**. There is no
"majority vote"; conflicts resolve by defined precedence, and the engine emits the
first applicable deterministic effect.

## 4. Decision precedence (a DENY always wins)

1. Blocked category / blocked rule → `DENY`.
2. Identity invalid / no valid mandate → `DENY` (fail closed).
3. Exceeds human-approval threshold → `HUMAN_APPROVAL_REQUIRED`.
4. Exceeds step-up threshold / suspicious → `STEP_UP_AUTHENTICATION`.
5. Within all caps and hours and allowed categories → `ALLOW`.

## 5. Rule evaluation (example)

Facts: `{agent: shopping-agent, amount: 6500, category: electronics, hour: 14:00,
agent_daily_spend: 8200, merchant: ABC-Store}`.

- Category `electronics` not in allowed `[food,grocery,household]` → **DENY**.

Facts: `{amount: 2500, category: food, hour: 11:00, agent_daily_spend: 2000}`.
- Allowed category, within per-txn (2500 ≤ 3000), daily (4500 ≤ 10000), hours OK.
- `amount 2500 > human_approval_above 2000` → **HUMAN_APPROVAL_REQUIRED**.

Facts: `{amount: 900, category: food, hour: 13:00, daily: 100}`.
- All in-bounds → **ALLOW**.

## 6. Precedence & conflicts

- Rules have an explicit `precedence` integer. Lower number = higher priority.
- If two same-priority rules conflict, the `DENY`/`REQUIRE_APPROVAL` effect wins over
  `ALLOW` (fail-closed bias), and the engine logs the ambiguity as a policy-quality
  signal for the `policy_admin`.

## 7. Versioning & rollback

- Each change creates `policy_versions` row with a `checksum`.
- The engine always evaluates the **latest effective version** for the merchant/agent,
  unless a transaction pins to a specific version (needed for passport replayability).
- Rollback: set effective pointer to a prior version; audited.

## 8. Agents cannot self-elevate

- Only `merchant_users` with the `policy_admin` role can edit policy (via dashboard).
- Any policy change is versioned + audited. An agent cannot invoke any policy tool.
- Even if the LLM tries, there is no tool that modifies policy. (Invariant 6.)

## 9. Failure & availability

- Evaluate synchronously in the decision path with a strict deadline.
- If policy engine is unavailable → **DENY / escalate (fail closed)**, never allow.
- Policy evaluations are cached only where inputs are immutable per version; the cache
  is keyed by facts hash + policy_version.

## 10. Observability & testing

`policy.decision` events, denial rate, decision latency, conflict signals. Unit test:
a large table of (facts → expected decision) edge cases including all precedence and
fail-closed paths.

## 11. Why a DSL and not just code or JSON rules

A restricted typed DSL (+ JSON for portability) gives deterministic semantics,
versioning, human readability in the merchant dashboard, and prevents procedural
hacks. Rejected: free-form rule scripts (unreviewable, non-deterministic, injection
risk); hardcoding (not merchant-configurable).
