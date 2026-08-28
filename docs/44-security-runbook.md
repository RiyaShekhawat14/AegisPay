# 44 — Security Runbook

## 1. Prioritized SEV for security

- **S-SEV1:** unauthorized money movement, cross-tenant breach, PII leak, credential
  compromise of a money path, webhook forgery that altered state.
- **S-SEV2:** prompt-injection surfacing into a near-money action, agent credential
  abuse flagged, secrets exposure, red-team failure in CI.

## 2. Containment playbook

1. **Freeze first:** disable payment/refund origination for the affected tenant(s) and
   suspend the implicated agent(s) — fail-closed.
2. **Preserve evidence:** snapshot `audit_events`, webhook raw events (S3), and the
   passport; do not mutate.
3. **Scope:** determine blast radius (tenant, transaction, agent, credit).
4. **Isolate:** revoke credentials, block API keys, revoke the webhook path if suspect.

## 3. Common incidents

### 3.1 Prompt injection → attempted unauthorized payment
- Evidence: DENY-rich audit with injection-classified attempts.
- Contain: suspend the agent; disable its tool scope; exclude flagged catalog items.
- Verify: no payment was created; the DENY recorded; passport shows intended-not-paid.
- Recovery: re-enable after controls confirmed; alert the merchant.

### 3.2 Credential leak (agent/merchant key)
- Revoke + rotate immediately; invalidate sessions. Verify no money action used it.

### 3.3 Secret in logs/repo
- Rotate the credential; scrub the log/S3; enable secret scanning; block the diff.

### 3.4 Cross-tenant access attempt
- Confirm RLS blocked (query returns empty); verify no row leaked; harden app-layer
  tenant context; add a regression isolation test; check audit.

### 3.5 Webhook forgery / replay
- Verify signature path; check if a forged event changed state; if so → SEV1,
  re-run the ledger verifier + reconciliation to restore true state.

### 3.6 Recon (scan, enumeration)
- Normal DDoS/scan: WAF + rate-limits. No immediate containment.

## 4. Evidence & audit

- Every containment action is itself audited (who did what, when, scope).
- The audit chain verifier is run to ensure no tampering; export relevant segment for
  legal/compliance if required.

## 5. Post-incident

- Root cause + the invariant that failed (if any) + detection gap.
- Add/strengthen a red-team scenario + detection alert.
- Consider a blast-radius review: was the agent able to reach more than it should?
  Tighten scopes.

## 6. Tooling

- CloudTrail (AWS control-plane), audit ledger + verifier, webhook signature metrics,
  injection classifier hits, authz-denial spike alarms, DLQ depth, secret scan, SIEM
  via CloudWatch.

## 7. Contacts & escalation

- On-call security contact (rotating); legal/compliance for PII or financial incidents;
  provider (Razorpay) contact for provider-side anomalies. Always document the
  hand-off.
