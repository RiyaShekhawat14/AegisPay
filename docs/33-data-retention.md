# 33 — Data Retention

## 1. Principle

Retain only what is needed for operation, audit, and compliance; delete/redact the
rest. Payment and audit data are retained (often legally required); PII is minimized
and pruned aggressively.

## 2. Retention table (defaults, configurable)

| Dataset | Default retention | Notes |
|---|---|---|
| Raw webhooks (S3) | 90 days | then purge; metadata kept |
| Webhook event metadata | 180 days | raw in S3; metadata referenced |
| Payments / attempts / refunds | 6 years | needed for reconciliation/audit/disputes |
| Orders / intents / carts | 6 years (audit) | carts pruned at 90d if not converted |
| Audit ledger (audit_events) | 6 years (configurable) | → S3 export; anchored |
| Transactions / passport | 6 years | evidence |
| Risk assessments | 6 years | evidence |
| Customer PII fields | while customer active + a short tail (e.g., 30–90d after deactivation) | then redact/delete |
| Agent/session logs | 90 days | operational |
| Daily logs (CloudWatch) | 14–30 days | operational |

## 3. Hard-delete vs soft-delete

- Hard-delete (or redact) PII after the tail window where feasible.
- Financial/audit/transaction rows are **soft-delete/immutable** (never purged) to
  preserve evidence; on purge of raw data the *hash* remains.
- Never `DELETE` from `audit_events`, `payments`, `idempotency_keys`, `webhook_events`.

## 4. Data minimization

- Only store required PII (email/phone/name/address as needed); tokenize identifiers
  where possible; store opaque refs and hashes preferentially.
- LLM context never receives raw PII; agents get minimized/aggregated data.

## 5. Deletion

- GDPR/DPDP-style right-to-delete: a deletion job identifies the subject's data,
  redacts PII fields and the raw sensitive text, keeps necessary audit evidence
  (anonymized), and records the deletion event in the audit ledger.
- Retention jobs run on schedule; deletion is logged for audit.

## 6. Access control

- Retention/export jobs run with least-privilege, scoped roles; export is gated and
  denied for raw PII by default.

## 7. Compliance honesty

We align to a minimization/retention discipline and reference DPDP-style obligations
without asserting legal compliance; a qualified review is a launch gate (see
`docs/34`, `docs/36`).
