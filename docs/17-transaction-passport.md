# 17 — Transaction Passport

## 1. Purpose

The Transaction Passport is AegisPay's signature feature: a single, verifiable bundle
that proves what a transaction was, who authorized it, under which policy/risk, on
which provider, and whether the audit chain is intact. It is the "receipt" and the
"court file" in one.

## 2. Fields

```
transaction_id        agent_id        merchant_id      user_id
intent_hash           cart_hash       authorization_hash
policy_version        risk_score     protocol         authorization_method
human_presence        spending_limit  decision         provider
provider_order_id     provider_payment_id
previous_event_hash   current_event_hash
timestamp(s)
```

## 3. Hash / sign / store / verify — what goes where

We **do not invent cryptography**. The design uses salted SHA-256 for integrity hashes
and HMAC-SHA256 only for the audit-chain signature. Explicitly:

| Item | How | Why |
|---|---|---|
| `intent_hash` | SHA-256 of canonicalized, versioned intent | Binds "what was proposed" to "what was authorized" |
| `cart_hash` | SHA-256 of ordered line items + prices | Binds "what was in the cart" (cart-tamper guard) |
| `authorization_hash` | SHA-256 of the bound authorization (scope, mandate, amount, nonce) | Binds the user/mandate grant to this transaction |
| `policy_version` | stored reference | which immutable policy version ran |
| `risk_score` / `risk_level` | stored + factors hash | explainable, auditable risk |
| `decision` | stored + included in hash | ALLOW/DENY/APPROVAL/STEPUP |
| `provider_order_id`/`payment_id` | stored | provider conviction reference |
| `previous_event_hash`/`current_event_hash` | part of audit chain | tamper-evidence linkage |
| display metadata (names, timestamps) | **stored, not signed** | cosmetic/provenance; no security value |

**What is signed:** the decision-critical inputs (`intent_hash`, `cart_hash`,
`authz_hash`, `policy_version`, `risk_score`, `decision`, `provider_order_id`) are
bound into the audit-chain `event_hash`+`event_signature`. This makes forged or
substituted values detectable.

**What is merely stored:** human-readable labels, timestamps, protocol/authorization
method descriptors, and the risk *display* (factors are hashed for integrity but
readable for humans).

## 4. The chain of custody

```
User Intent ─→ Intent_hash
Cart        ─→ Cart_hash
Authorization = f(mandate, amount, nonce, expiry) ─→ authz_hash
Policy(version) ─→ decision
Risk ─→ score/factors
Passport = H(intent_hash, cart_hash, authz_hash, policy_version, decision, provider_order_id)
   bound into audit_events → hash chain → anchor
```

## 5. Replay / tamper proofing (what the passport stops)

- **Cart tampering:** if line items/prices differ from the bound `cart_hash`, the
  authorization is invalid → rejection. (Invariant 5.)
- **Authorization theft/replay:** authz is bound to a nonce + scope + expiry + the
  specific transaction digest; reusing it for a different cart/intent fails hash match.
- **Approval replay:** the human approval is single-use & scope-hashed (see `docs/12`).
- **Decision substitution:** the signed decision cannot be silently changed.

## 6. Retrieval & verification

- `GET /v1/transactions/{id}/passport` returns the full bundle; the UI shows
  `Audit Integrity: VERIFIED` (chain intact) or `FAILED` (alert).
- The passport regenerates the hashes from stored canonical inputs and checks them
  against the audit chain to prove nothing was altered after commit.

## 7. UI example

```
TRANSACTION PASSPORT
Transaction:  txn_82931      Agent: shopping-agent-v3     Merchant: ABC Store
User Intent:  "Buy running shoes under ₹4,000"
Intent Hash:  abc…  Cart Hash: def…  Authorization: VALID
Policy: policy_v12      Risk: 21 / LOW (factors shown)
Human Approval: NOT REQUIRED     Spending Limit: ₹10,000/day
Protocol: A2A   Auth Method: OIDC mandate   Decision: AUTO_APPROVE
Provider: Razorpay   Order: order_xxx   Payment: SUCCESS
Audit Integrity: VERIFIED  ·  Chain: evt_1 → evt_2 → … → anchor
```

## 8. What the passport deliberately does NOT do

- It does **not** store card numbers/tokens or provider secrets.
- It does **not** claim external legal validity; it is an engineering-grade provenance
  record, not a notarized proof. We avoid inventing "cryptographic notarization".

## 9. Cross-cutting

Passport is produced on every decision path (authorized, approved, denied — so even a
denied attempt has an auditable passport). It is the answer to "can we explain every
financial decision?" → **yes**, via policy version + reason trail + risk factors +
authz bound + audit chain.
