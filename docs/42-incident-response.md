# 42 — Incident Response

## 1. Severity

- **SEV1 / Critical:** potential or actual unauthorized money movement, duplicate
  charge, cross-tenant breach, PII leak, payment reconciliation stuck across many
  transactions.
- **SEV2 / Major:** payment outage, webhook pipeline failing, policy/risk engine down
  (fail-closed reducing availability), queue/DLQ large.
- **SEV3 / Minor:** degraded latency, non-critical alert.

## 2. Response flow

```
Detect (alert/dashboard) → Triage (SLO, impact) → Contain (fail-closed, pause) 
→ Investigate (traces/logs/passport) → Fix (rollback/flag/abort) 
→ Recover (reconcile/replay) → Verify (chain verifier) → Learn (postmortem)
```

## 3. Immediate actions (money + security)

- **Duplicate-charge / unknown-stuck:** disable payment origination for the affected
  tenant(s) (fail-closed); start reconciliation; do not blind-retry.
- **Webhook signature failures:** verify signature logic, provider keys, and check for
  attack; quarantine events; do not process.
- **Source in a deploy:** roll back the task set (blue/green) / revert the feature flag.
- **DB/Redis issue:** fail-closed; money actions rejected until dependencies are healthy.

## 4. Investigation primitives

- Trace: full span from user→agent→tool→policy→risk→authz→payment→webhook→reconcile.
- Passport: retrieve the transaction bundle; verify hashes + chain.
- Audit: query `audit_events` by `correlation_id`/`transaction_id`; check chain verifier.
- Reconciliation report: unknown-rate, mismatch list.

## 5. Communication

- SEV1: page on-call + notify merchant contact + legal/compliance as applicable.
- Status page for providers/merchants; clear, honest, no invented details.

## 6. Postmortem

5-whys; classify (config/code/dependency/human); identify the **invariant that failed**
(if any) and the detection gap; add regression + red-team test; track to closure.
Every postmortem must state the honest residual risk.

## 7. Escalation & ownership

Assign a single incident commander; on-call rotation; a `docs/43-runbook` for known
scenarios; `docs/44-security-runbook` for security incidents.
