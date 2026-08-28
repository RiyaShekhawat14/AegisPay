# 31 — Event Catalog

Domain events, CloudEvents-style envelope. **Events double as audit records** (same
writer), so every business event is automatically append-only and hash-chained.

## 1. Envelope

```json
{
  "event_id": "evt_01J...",
  "event_type": "commerce.order.created",
  "schema_version": "1.0",
  "timestamp": "2026-08-27T09:12:33.000Z",
  "tenant_id": 101,
  "correlation_id": "corr_...",
  "causation_id": "evt_01J-parent",
  "trace_id": "trace_...",
  "actor": "agent:shopping-agent-v3",
  "actor_type": "AGENT | USER | SYSTEM | WEBHOOK",
  "payload": { "...": "..." },
  "previous_hash": "abc...",
  "event_hash": "def...",
  "event_signature": "<hmac>"
}
```

`event_id` is a UUIDv7 (time-ordered). `correlation_id` spans a logical request/journey;
`causation_id` points to the prior event that caused this one (event causality).

## 2. Event types

### Commerce (intent/cart/order)
- `commerce.intent.created` — payload: `intent_id, agent_id, user_id, intent_hash`.
- `commerce.intent.rejected` — `intent_id, reason, policy_version`.
- `commerce.cart.created` — `cart_id, cart_hash, customer_id, agent_id`.
- `commerce.cart.updated` — `cart_id, cart_hash, item_count, total_minor`.
- `commerce.cart.locked` — `cart_id, cart_hash, expires_at`.
- `commerce.order.created` — `order_id, cart_id, intent_id, total_minor, policy_version`.
- `commerce.order.approved` — `order_id, approval_id`.
- `commerce.order.rejected` — `order_id, reason`.

### Payment
- `payment.initiated` — `payment_id, order_id, provider, provider_order_id, amount_minor`.
- `payment.pending` — `payment_id, provider_payment_id`.
- `payment.succeeded` — `payment_id, provider_payment_id, capture_id, amount_minor`.
- `payment.failed` — `payment_id, provider_payment_id, failure_reason`.
- `payment.unknown` — `payment_id, reason(provider_timeout|no_webhook)`.
- `payment.reconciled` — `payment_id, result(CAPTURED|FAILED|STILL_UNKNOWN), attempts`.

### Approval
- `approval.requested` — `approval_id, order_id, amount_minor, scope_hash, expires_at`.
- `approval.approved` — `approval_id, approver_user_id, decision_hash`.
- `approval.rejected` — `approval_id, approver_user_id, reason`.
- `approval.expired` — `approval_id`.

### Policy / Risk
- `policy.evaluated` — `target_type, target_id, decision, policy_version, rule_precedence`.
- `policy.denied` — `target_type, target_id, rule_id, dimension, reason`.
- `risk.escalated` — `target_type, target_id, score, level, recommended_action`.
- `risk.assessed` — `target_type, target_id, score, factors, model_version`.

### Security / Audit-adjacent
- `agent.authenticated`, `agent.action`, `agent.credential.rotated`,
  `agent.credential.revoked`, `authz.issued`, `authz.expired`, `authz.rejected`,
  `audit.anchor` (checkpoint).

### Webhook / Reconcile
- `webhook.received`, `webhook.verified`, `webhook.deduped`, `webhook.failed`.
- `reconciliation.started`, `reconciliation.completed`, `reconciliation.escalated`.

### Campaign / Growth
- `campaign.created`, `campaign.action.executed`, `campaign.budget.exceeded`.

## 3. Versioning

- `schema_version` is monotonically increasing per `event_type`.
- Additive changes are backward-compatible (new optional fields); consumers must be
  tolerant.
- Breaking changes use a new `event_type` (e.g., `commerce.order.created.v2`) with a
  documented migration window and dual-write during the transition. We never mutate
  past event payloads (append-only).

## 4. Delivery semantics

- **Emit:** in the same DB transaction as the state change (acidic guarantee), via an
  outbox table to avoid "committed but not emitted" and never "emitted but not committed".
- **Consume:** at-least-once; consumers must be idempotent (dedupe by `event_id`).
- **Retention/backpressure:** DLQ per consumer; poison messages isolated and alerting.

## 5. Audit note

Because events are the audit records, an event is written exactly as the state
mutation commits. Event hashing (previous/current) forms the tamper-evident chain
described in `docs/16-audit-ledger.md`.
