# 12 — Authorization Model

## 1. Purpose

Authorization answers **two distinct questions**, both required before money moves:

1. **Has the *user/agent* authorized this agent to spend?** → `customer_authorization`
   / `mandate` (scope, value limits, validity).
2. **Has the *AegisPay control plane* authorized this specific transaction?** →
   transaction-bounded authorization issued after policy + risk.

Separating consent-to-act from permission-to-move-money is what defeats authorization
theft and replay: a stolen token or replayed mandate cannot by itself fund a payment,
because the platform authorization is bound to the specific transaction digest.

## 2. Authorization architecture

### 2.1 Grant (consent layer, long-lived)
- `customer_authorizations`: a customer grants an agent a bounded mandate.
- Fields: `scope` (categories/types), `upper_value_limit`, `per_txn_limit`, `valid_from`,
  `valid_to`, `status`, `mandate_hash` (signed terms).
- Revocable. This is the *ceiling* for what the agent may spend on this customer's behalf.

### 2.2 Transaction authorization (per-transaction, short-lived)
- `authorization` object bound to one `(intent_hash, cart_hash, amount, currency,
  agent, merchant, customer, nonce, policy_version, risk_score, expires_at)`.
- Issued only if policy is `ALLOW` (or approval granted) and risk is within bounds.
- **Single-use** per transaction digest; expires; cannot be re-applied to a changed
  cart/intent (hash mismatch → invalid). This is Invariant 5 + Invariant 7 partially
  (for approvals).

## 3. Binding & validity

- Authorization is **bound** to the transaction, not to a generic "customer can buy":
  `authorization_hash = H(cart_hash, intent_hash, amount, mandate_hash, nonce, expiry)`.
- If the cart changes materially (quantity/price/items) → `cart_hash` changes →
  authorization invalid → re-authorize. It never silently re-validates.

## 4. What invalidates an authorization (checked by a guard)

- Any field in the binding changes.
- Expiry reached.
- Mandate revoked / customer turned off.
- Agent suspended/revoked.
- Policy version no longer applicable (or risk level changed beyond threshold).

## 5. Fail closed

- Unavailable authorization service → **deny** (new money actions blocked).
- Any ambiguity → deny/escalate. No "probably fine" path.
- **Product ownership is a binding input.** Authorization is only valid if every cart
  item's product belongs to the target merchant (`tenant_id` matches). A cross-merchant
  or tenant-mismatched product makes the authorization invalid — this is part of the
  transaction binding, not a separate check to skip.

## 6. Replay & theft defenses

| Threat | Defense |
|---|---|
| Stolen mandate | Transaction authz requires fresh binding to THIS transaction's digest |
| Replay of an authz | single-use nonce + expiry + one-time binding |
| Authorization theft | binding includes agent/customer/mandate; cross-binding mismatch → deny |
| Cart substitution | cart_hash in binding; mismatch → invalid |
| Cross-tenant | authorization is tenant-scoped; RLS + tenant context |

## 7. Non-repudiation

- The authorization issuance is written to the audit ledger as a signed event.
- Who approved (for HITL) is bound into `approval_decisions` with the approver and a
  `decision_hash` matching the `authorization_hash`/`scope_hash`.

## 8. Sources of truth

- User/mandate: `customer_authorizations`, `mandates`.
- Platform: `authorization` (transaction-bound), `approval_requests`/`approval_decisions`.
- There is **no** authority in the agent or LLM. The LLM can *request* authorization;
  it cannot *grant* it.

## 9. Human-in-the-loop (HITL) — this doc's sibling

See §18 of the master doc and `docs/17`/`docs/12` interplay. Summary:
`LOW → auto-approve`, `MEDIUM → step-up`, `HIGH → human approval`, `CRITICAL → deny`.
Approval requests: `scope_hash`, `expires_at`, `require_approver_role`. Decisions are
single-use, scope-bound, non-replayable, non-stale, audited. Reuse of an approval →
rejected (scope hash mismatch / used already / expired). This prevents privilege
escalation via approval and stale approvals.

## 10. Decision contract

The authorization engine returns a bounded result:

```
Autorize → { status: ALLOWED | APPROVAL_REQUIRED | DENIED
             authorization_hash, expires_at, policy_version, risk_level }
```

Delivered back to the orchestrator, which then may (a) proceed to payment, (b) raise
an approval request, or (c) record a denial — each with an audit event.
