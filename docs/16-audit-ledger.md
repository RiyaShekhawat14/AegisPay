# 16 — Audit Ledger

## 1. Purpose

An append-only, hash-chained, tamper-evident record of every important action. It is
the source of truth for "who authorized what, when, and why." It combines with the
Transaction Passport to produce non-repudiation.

## 2. Event schema (shared with the event catalog)

See `docs/31-event-catalog.md` for the envelope. Key fields: `event_id, tenant_id,
event_type, actor, actor_type, correlation_id, causation_id, trace_id, payload,
previous_hash, event_hash, event_signature, created_at`.

## 3. Tamper-evidence design

- **Event hash chain:** `event_hash = SHA-256(previous_hash || event_id || event_type ||
  tenant_id || timestamp || payload_hash)`.
- `previous_hash` points to the prior event for the same tenant/chain. Altering a past
  event invalidates all subsequent hashes → detectable.
- **Keyed signature:** `event_signature = HMAC-SHA256(ledger_key, event_hash)` provides
  non-repudiation (only the ledger-key holder can sign). The key is in the secrets
  layer, never the DB.
- **Anchor/checkpoint:** periodically, an `audit.anchor` event is pinned to an
  immutable external root (S3 object with a timestamp + hash). Rewriting a past event
  breaks the chain and its relationship to the anchor → tamper evidence survives a full
  DB compromise.

## 4. Immutability

- RLS policy: **read-only** for `audit_events` (no `UPDATE`, no `DELETE` grants).
- `audit_events` and `audit_event_hashes` are **never** soft-deleted.
- Writing goes through the audit writer service only; no entity bypasses it.

## 5. Atomicity

- The audit event is written **in the same DB transaction** as the state change it
  records. You can never have a payment/order state change without a matching audit
  record, and never an audit record for a state change that was rolled back.

## 6. Actor model

`actor_type ∈ USER | AGENT | SYSTEM | WEBHOOK | CRON`, with `actor` being the id and a
descriptive label. Every decision is attributable to a concrete actor.

## 7. Correlation

Every event carries `correlation_id` (journey) and `causation_id` (causality). This is
how you reconstruct a full timeline for a transaction or a suspicious attempt.

## 8. Retention & export

- Retention configurable (default ≥6 years for financial/audit; adjust per policy, see
  `docs/33-data-retention.md`).
- Export to S3 for regulators/compliance on demand (bulk snapshot of a tenant's ledger).

## 9. What is NOT recorded (and why)

Raw provider secret keys, full card data, and customer secrets are **not** recorded —
they carry zero auditing value and create liability. Only the *hash* of sensitive
inputs is stored (e.g., request/payload hash). This is both a privacy and security
requirement.

## 10. Verification

- A **verifier** recomputes the hash chain for a tenant/range and reports any mismatch
  as a security event + alert (run on a schedule and on demand from the passport UI).
- The Transaction Passport surfaces `Audit Integrity: VERIFIED` when the chain from the
  transaction's first event to its anchor is intact.
