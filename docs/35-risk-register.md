# 35 — Risk Register

Open technical/operational risks, scored (Likelihood × Impact), with owner & mitiga-
tion. This is a living register; NOT a claim about residual risk being zero.

## 1. Financial

| ID | Risk | L | I | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| FR-1 | Duplicate charge on ambiguous provider result | Med | High | High | idempotency + UNKNOWN→reconcile + no blind retry | Payment |
| FR-2 | Over-limit agent spend | Med | High | High | deterministic policy caps + daily/per txn + risk | Policy |
| FR-3 | Refund amount/duplicate abuse | Low | High | Med | refund capped to captured + single per key + policy | Payment |
| FR-4 | Margin destruction via AI discount | Med | Med | Med | campaign margin floor + discount cap | Growth |
| FR-5 | Dispute / chargeback with no evidence | Med | Med | Med | signed passport + audit chain | Trust |

## 2. Security

| ID | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|
| SR-1 | Prompt injection → over-limit spend | High | High | **Critical** | catalog DATA-only, allowlist tools, deterministic policy, red-team |
| SR-2 | Authorization replay / theft | Med | High | High | transaction-bound authz, nonce, expiry, single-use |
| SR-3 | Webhook forging/replay | Low | High | Med | HMAC verify + timestamp + dedupe + idempotent apply |
| SR-4 | Cross-tenant data leak | Med | High | High | RLS + tenant context + isolation tests |
| SR-5 | Secrets/credential leak | Low | High | Med | Secrets Manager, no config in image, redaction |
| SR-6 | Agent privilege escalation | Low | High | Med | no policy tool for agents; RBAC; audited changes |

## 3. Data / privacy

| ID | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|
| DR-1 | PII breach | Med | High | High | minimization, field encryption, scoped access, DLP |
| DR-2 | Audit tampering | Low | High | Med | append-only RLS read-only + hash chain + S3 anchor |
| DR-3 | Retention overflow / privacy gap | Med | Med | Med | retention jobs, redaction, deletion logs |

## 4. Reliability / operations

| ID | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|
| RR-1 | Payment unknown-stuck | Med | High | High | reconciliation + escalation + manual queue + alerts |
| RR-2 | Provider/DB/queue outage | Med | High | High | circuit breakers, fail-closed, backups, DR |
| RR-3 | Policy/risk engine outage | Med | High | High | fail-closed (deny/escalate) |
| RR-4 | Reconciliation blind-retry | Low | High | Med | code rule + tests; no create-on-unknown |
| RR-5 | LLM/tool latency hurting UX | Med | Med | Med | budgeted latency, async where safe, optimistic UI |

## 5. Protocol / ecosystem

| ID | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|
| PR-1 | Standard churn (MCP/A2A/UAP) | High | Med | Med | adapter layer → canonical model; don't couple core |
| PR-2 | Compliance claim challenge | Low | High | Med | no compliance claims; honest maturity table |

## 6. Residual / acknowledged

- Region-loss DR (single-region v1): accepted risk, documented, cross-region deferred.
- The LLM can still be *socially engineered* to make a bad *proposal* (e.g., a
  suboptimal recommendation) — that's bounded & audited; it cannot be *authorized*
  outside policy. This is the deliberate design: reduce the blast radius, not the
  agent's thinking ability.
