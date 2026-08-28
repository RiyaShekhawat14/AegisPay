# 14 — Webhook Architecture

## 1. Purpose

Webhooks are **untrusted external events**. Razorpay (or any provider) may send
duplicates, out-of-order, delayed, replayed, or forged events. The webhook pipeline
turns hostile/channel-noisy input into an idempotent, authoritative state driver.

## 2. Pipeline

```
Razorpay
   ↓
Webhook Gateway (ALB/WAF, TLS)
   ↓
Signature Verification   ← HMAC over payload, constant-time compare
   ↓
Timestamp Validation     ← reject stale events outside a window
   ↓
Replay Detection         ← event id / webhook id dedupe
   ↓
Persist Raw Event        ← S3 (raw) + webhook_events (metadata), status RECEIVED
   ↓
Dedup                    ← unique (provider, provider_event_id); duplicates → DEDUPED, no-op
   ↓
Queue                    ← durable, at-least-once, retry with backoff
   ↓
Webhook Processor        ← apply to Payment/Order state machine, idempotently
   ↓
Audit                    ← append-only event
```

## 3. Signature verification

- Compute HMAC-SHA256 over the raw body with the provider webhook secret; compare
  constant-time (`hmac.Equal` or `subtle.ConstantTimeCompare`).
- On mismatch → reject with `WEBHOOK_INVALID_SIGNATURE`, record event, alert, do not
  process. Invalid signatures are a **security event**, not a transient error.
- Secrets from the secrets layer; no secret in logs.

## 4. Timestamp validation

- Reject events older than `now - window` (default 5–15 min) unless the event id is
  already known → stale event is a no-op or triggers reconciliation, never a state jump.

## 5. Replay & dedup

- Dedupe key: `(provider, provider_event_id)`. Unique constraint prevents two inserts.
- If an event arrives again: return `200 OK` (idempotent acknowledgement), status
  `DEDUPED`, no state change, no second side effect.

## 6. Out-of-order / delayed

- The processor applies events through the **state machine**, which is idempotent and
  rejects illegal transitions. A delayed "created" after a "paid" is a no-op or a
  reconciliation trigger, not a regression.
- Payment state is the **max-progress** state; a stale event cannot move a
  `SUCCESS` payment back to `PENDING`.

## 7. Retry & DLQ

- Processor retries with exponential backoff + jitter on transient errors; poisoned
  (permanently failing) events go to a **dead-letter queue** with alerting and manual
  replay. Idempotency prevents double-application on replay.

## 8. Processing semantics

- Applying a webhook computes deterministic transition(s) to the payment/order state;
  if the new state conflicts with current, the processor marks the event `APPLIED` or
  `STALE` and emits an observability signal. It never throws away without a record.

## 9. Failure matrix

| Scenario | Behavior |
|---|---|
| Forged signature | reject, alert, do not process |
| Duplicate event | idempotent ack, no-op |
| Out-of-order | state-guard no-op or reconcile |
| Delayed | reconcile after grace, no blind apply |
| Malformed | 4xx/DLQ, alert, no crash |
| Provider outage | events buffered, retry, backpressure, DLQ eventually |

## 10. Observability

Webhook received/verified/deduped/applied/failed per provider, signature-failure rate,
duplicate rate, per-event latency, DLQ depth. Alerts on signature failures, stuck
unknown payments, and DLQ growth.

## 11. Security & audit

- Webhooks never authenticate as an agent; they are a separate, minimal-permission
  path that only renders provider state.
- Full event timeline recorded (received→verified→applied) in the audit ledger.
