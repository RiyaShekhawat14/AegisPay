# 08 — Threat Model (STRIDE-oriented)

Assets: Money, Authorization (mandates), Agent credentials, Merchant credentials,
Customer PII, Policies, Catalog, Orders/Payments, Audit trail, Transaction Passport.

## 1. Spoofing — attacker masquerades as a trusted principal

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| Agent impersonation | Use a stolen/recreated agent key | unauthorized spend | Medium | hashed+rotatable credentials, mTLS, session binding, canonical id mapping | auth anomalies, failed auths | revoke, quarantine, re-issue | Low |
| Merchant user impersonation | Phish a merchant OIDC/PW; stolen session | policy change, refund | Medium | OIDC + MFA, short-lived sessions, step-up for sensitive ops | odd-time logins, MFA challenges | force re-auth, revoke sessions | Low |

## 2. Tampering — unauthorized modification of data

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| Cart tampering | edit qty/price after approval | wrong amount charged | Medium | server-authoritative cart, cart_hash binding | hash mismatch | invalidate authz, re-authorize | Low |
| Price manipulation | agent claims lower price | underpay/harm | Medium | server-side price from catalog | price ≠ catalog | reject & audit | Low |
| Audit tampering | rewrite past events | cover tracks | Low | append-only + RLS read-only + hash chain + anchor | verifier mismatch → alert | restore from anchor/immutable source | Very low |
| Log/secret leak | exfiltrate secret | full compromise | Low | no secrets in logs; redaction; Secrets Manager | secret scan, SIEM | rotate, revoke | Medium |

## 3. Repudiation — deny having done something

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| Disputed charge | merchant/customer denies authorization | dispute, loss | Medium | signed authz + passport + approval chain, non-repudiable | passport verification | present evidence | Low |
| Fake authorization | claim an authz that didn't happen | fraud | Low | signed event with actor + timestamp | passport/audit integrity | escalate | Low |

## 4. Information disclosure

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| PII exfiltration | agent dumps customer data | privacy breach, regulatory | Medium | minimization, scoped reads, no PII to LLM, encryption, redaction | anomalous data pulls, DLP | isolate, rotate, notify | Low |
| Cross-tenant read | tenant A queries tenant B | data breach, policy violation | Medium | RLS + tenant context + param queries | isolation tests, RLS assertions | block, audit | Low |
| Catalog poisoning | malicious product text | injection/disinfo | Medium | DATA vs INSTRUCTIONS, allowedlist, injection classifier | flag unsafe content | exclude product, audit | Low |

## 5. Denial of service

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| Agent DoS (spend/hammer) | too many tool calls/carts | load + misuse | Medium | rate limit, action budget, caps | rate-limit alerts, load | throttle/suspend | Low |
| Webhook flood | flood with invalid/replayed events | queue waste | Medium | signature verify, dedupe, rate limit | DLP/dedup metrics | drop, DLQ | Low |
| Payment cost DoS | exploit refund/paid mismatch | financial | Low | reconciliation, refund caps | reconciliation alerts | hold/pause | Low |

## 6. Elevation of privilege

| Threat | Attack | Impact | Likelihood | Mitigation | Detection | Recovery | Residual |
|---|---|---|---|---|---|---|---|
| Agent modifies own policy | call a policy-change tool | unrestricted spend | Low | no such tool; only policy_admin; RBAC | attempt flagged | deny, audit, revoke | Very low |
| Stolen mandate → elevate | use a limit-exceeding token | over-limit spend | Medium | transaction-bound authz, daily/per txn limits | value-bucket anomalies | block | Low |
| Replay approval | reuse an old approve | second spend | Medium | single-use, scoped, expiring | duplicate decision detect | reject | Low |
| Protocol bypass | drive payment directly via A2A/MCP | bypass policy | Medium | adapters → canonical → policy always; no direct money path | audit that path resolves through pipeline | block adapter | Low |

## 7. Prioritization (highest concern)

Ranked by who controls money and how hard it is to detect:

1. **Prompt injection → over-limit spend** (must be blocked; core demo).
2. **Authorization replay/cross-binding** (invariant).
3. **Cart/price tampering after authz** (invariant).
4. **Cross-tenant leakage** (RLS + tests).
5. **Duplicate payment on ambiguous provider outcome** (reconciliation).
6. **Fake/replayed webhook** (signature + dedupe).
7. **Agent privilege escalation** (no tool, RBAC).
8. **Audit tampering** (chain + anchor).
