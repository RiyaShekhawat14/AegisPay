# 43 — Runbook

Operational runbook for the money path. **Golden rule: never blind-retry an unknown
payment; never allow without policy.**

## R1 — Payment stuck UNKNOWN (reconciliation)
- Look at `reconciliation_jobs`; is the worker running? check `next_attempt_at`.
- Check provider via Razorpay dashboard for the `provider_order_id`.
- If worker stalled: restart worker task; jobs resume (idempotent).
- If at max attempts & escalated: follow the manual reconciliation path; a human
  records `CAPTURED`/`FAILED`. Never re-run create.

## R2 — Webhook signature failures rising
- Check `webhook_signature_failure_last_5m`; verify webhook secret is current in the
  secrets layer; confirm the provider webhook URL/env.
- If mismatch after key rotation → update secret, requeue. If still failing → treat as
  potential attack; isolate + alert security.

## R3 — Policy/risk engine unavailable (fail-closed is expected)
- Money actions are rejected (fail-closed). This is *correct* behavior. Restore the
  dependency; then let actions resume. Confirm the pass-through of expected DENY events.

## R4 — DB failover / RDS event
- RDS multi-AZ auto-failover; during the window new money actions are rejected.
- After failover, confirm RLS + tenants; run the chain verifier on the ledger.

## R5 — Redis unavailable
- Cache/locks/rate degrade; the money path reads/writes go through PostgreSQL.
- Check for rate-limit bypass risk; reinstate Redis; confirm locks not double-held.

## R6 — Queue / DLQ
- Inspect DLQ depth; view poison messages; replay (idempotent) or drop if irrecoverable.
- If the processor is down, restart; events re-consume at-least-once; dedupe holds.

## R7 — Campaign budget / margin breach alert
- Confirm campaign paused; verify `spent <= budget` and margin; notify merchant.
- Gap: no further discount apply on a breached campaign.

## R8 — Suspicious activity (possible injection/escalation)
- Pull the audit trail + passport; check for any DENY bypass, cross-tenant, or money-tool
  reach. If a bypass is found → SEV1; revoke the agent; checkpoint.

## R9 — Deploy rollback
- Revert the ECS task set (blue/green) or feature flag; confirm migrations were
  expand-phase so code rolls back safely.

## R10 — Restore drill
- Quarterly: restore a backup + PITR in staging; run the chain verifier + E2E; record RTO.

## On-call playbook cheat-sheet
- Money never calls provider re-`create`.
- UNKNOWN → reconcile, not retry.
- Fail closed, always, on doubt.
- Every decision is recoverable + explainable; use the passport.
