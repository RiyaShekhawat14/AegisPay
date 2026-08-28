# 15 — Reconciliation

## 1. Purpose

Reconciliation is how AegisPay resolves the dangerous `UNKNOWN` payment state. Its
**hard rule**:

> A payment in `UNKNOWN` is never blindly retried. You reconcile (look up the true
> provider state) before you act.

## 2. When a payment becomes UNKNOWN

- Provider call timed out (no response, no crash).
- Webhook not received within a grace window for an initiated payment.
- Provider returned an ambiguous/error verdict with no clear terminal state.

## 3. Reconciliation flow

```
Payment in UNKNOWN
   ↓
Reconciliation Worker picks job (poll / queue)
   ↓
BACKOFF: exponential + jitter (e.g., 1m,2m,4m,8m,30m,1h…)
   ↓
Provider lookup (FetchOrder/FetchPayment)  [idempotent, safe read]
   ↓
Result:
   CAPTURED/SUCCESS  → transition Payment→CAPTURED, Order→PAID, close job
   FAILED/cancelled  → transition Payment→FAILED, Order→FAILED, close job
   STILL_PENDING     → keep UNKNOWN, schedule next attempt (bounded)
   STILL_UNKNOWN     → escalate
   ↓
Bounded attempts (max 5) → escalate to MANUAL_RECONCILIATION (admin task/report)
```

## 4. Non-negotiables

- The worker **never** calls the *create* endpoint again. It only reads/fetches.
- A payment only leaves `UNKNOWN` on an authoritative provider verdict.
- If still unknown after max attempts, it **escalates**; money stays held; it is never
  auto-retried into a possible double charge.
- Reconciliation is idempotent: re-running a job on an already-resolved payment is a no-op.

## 5. Worker & DSL/params

- Jobs stored in `reconciliation_jobs` with `payment_id, job_no, attempts, max_attempts,
  next_attempt_at, result, escalated`.
- Selector: `WHERE status='PENDING' AND next_attempt_at <= now()`.
- Rate: per payment, serialized; never more than one in-flight job per payment.

## 6. Manual reconciliation

- When auto-reconciliation exhausts attempts, create a `MANUAL_RECONCILIATION` task with
  full context (passport preview + provider reference) and notify an ops/admin user.
- The human can verify against Razorpay dashboard and mark `CAPTURED` / `FAILED` /
  `REFUNDED`. Every manual decision is audited and signed.

## 7. Reporting

Reconciliation reports: unknown-rate by cause, attempts-to-resolve distribution,
escalation rate, manual decisions, and any mismatch (e.g., "we think paid, provider
says failed") as a **high-priority alert** — mismatches are financial safety signals.

## 8. Integration with success metrics

`reconciliation_success = resolved_auto / total_unknown`; launch gate ≥95% auto-resolve
with the remainder cleanly escalated.

## 9. Why not just retry?

Blindly retrying an unknown payment can double-charge: the first attempt may have
succeeded on the provider side, and a second create makes a second charge. Reconcile-
then-decide is the only safe resolution. This is Invariant 3.
