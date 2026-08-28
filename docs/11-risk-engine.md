# 11 — Risk Engine

## 1. Purpose

The risk engine produces an **explainable, bounded** risk score for a financial action.
It is layered, and the final authority is **never** the LLM. The LLM may only add a
qualitative note that is clearly separated and never overrides a deterministic rule,
policy DENY, or required human approval.

## 2. Output contract

```jsonc
{
  "risk_score": 78,
  "risk_level": "HIGH",                // LOW <40, MEDIUM 40-69, HIGH 70-89, CRITICAL 90-100
  "risk_factors": [
    { "name": "new_merchant", "weight": +30, "reason": "merchant account age < 30d" },
    { "name": "unusual_amount", "weight": +20, "reason": "amount 4x branch average" },
    { "name": "new_category", "weight": +15, "reason": "first time in electronics" },
    { "name": "new_device", "weight": +10, "reason": "unseen device fingerprint" },
    { "name": "trusted_agent", "weight": -5, "reason": "agent trust level HIGH" },
    { "name": "trusted_merchant", "weight": -2, "reason": "merchant in good standing" }
  ],
  "recommended_action": "HUMAN_APPROVAL_REQUIRED",
  "model_version": "risk-rules-v3.1"
}
```

## 3. Layers (kept separate)

| Layer | Nature | Authority | Notes |
|---|---|---|---|
| Deterministic rules | Hard signals | **Hard, non-overridable** | new merchant, unusual amount, new category/device, velocity, amount thresholds |
| Statistical base-rate | Historical + context | Weighted | baseline risk from that merchant/agent/category history |
| ML model score | Learned patterns | Weighted, never sole | from a trained model, `model_version` recorded |
| LLM reasoning | Qualitative note | **Non-authoritative** | summarized, separated, never toggles action |

**Fusion:** `score = clamp(rule_signals + statistical + w*ml)`; then the computed
`recommended_action` is **clamped by policy**: a score that says LOW cannot override a
policy DENY or a human-approval requirement. The LLM cannot down-rank a deterministic
high-risk factor.

## 4. Output → action mapping

| Level | Recommended action | Gated by |
|---|---|---|
| LOW | `ALLOW` (if policy also allows) | policy + authz |
| MEDIUM | `STEP_UP_AUTHENTICATION` | step-up |
| HIGH | `HUMAN_APPROVAL_REQUIRED` | approval |
| CRITICAL | `DENY` | deny (policy overrides everything) |

## 5. Explainability

- `risk_factors` gives a human-readable list with weight and reason.
- This is what the human approver sees in the approval inbox ("why is risk high?").
- Every factor is attributable to a concrete signal; nothing is a hidden "gut feeling".
- `model_version` lets you know which rules/model produced the score (regression
  tracing).

## 6. LLM isolation (important)

The LLM **cannot** be the final authority because it is probabilistic and manipulable.
A prompt-injected agent might produce a LOW-risk message, but the deterministic rule
signals and policy engine still govern the action. The LLM note is advisory and is
labelled as such in the passport.

## 7. Failure & availability

- If the risk engine is unavailable, the decision path **escalates by default**
  (fail-closed): require step-up/human approval, never auto-allow.
- Rule caching keyed by facts hash + version; ML score cached per
  `(merchant, agent, category, amount_bucket)`.

## 8. Observability

Risk score/level distribution, factor frequency (monitor for new-attack patterns),
escalation rate, model drift alert. Alerts: a sudden rise in MEDIUM/HIGH, an engine
outage, or a model-version change without review.

## 9. Testing

Unit: rule/score computation, clamping (LOW can't override DENY), edge thresholds,
LLM-note-isolation. Integration: full decision with policy + risk + authz. Red-team:
injected agents scoring LOW must still be blocked by deterministic signals.

## 10. Why separate layers

Fusing without separation is un-explainable (why did it score 78?). Separation lets a
merchant/a payments engineer read exactly *why*, and lets us degrade gracefully (rules
always on; ML optional). It mirrors how a payments risk team actually operates.
