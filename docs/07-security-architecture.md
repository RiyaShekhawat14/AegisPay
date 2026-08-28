# 07 — Security Architecture

## 1. Authentication

| Surface | Method |
|---|---|
| Merchant dashboard users | OIDC/OAuth (also supports password+MFA for bootstrap), session JWT with short TTL |
| Server-to-server (agent/merchant API) | scoped API keys (hashed, rotatable, tenant+agent-bound); mTLS for internal service identity |
| Agent protocols (MCP/A2A) | OAuth 2.1 client-credentials / OIDC subject → canonical `agent_id` |
| Webhooks | signature verification (provider HMAC), separate minimal-privilege path |

## 2. Authorization

- **RBAC** for dashboard users (`admin`, `ops`, `policy_admin`, `analyst`,
  `approver`); **ABAC** where it helps (role + merchant scope + resource attrs).
- **Scoped API keys** for agents/merchant integration (not all-powerful).
- Resource-level checks always include `tenant_id` (never rely on caller passing it).
- **Agent authorization** is separate from user RBAC: agent actions are constrained by
  scopes + allowed tools + policy + risk.

## 3. Secrets management

**Choice: AWS Secrets Manager** (see ADR-013). Secrets: Razorpay key/secret, DB
credentials, webhook secret, ledger HMAC key, encryption keys. Never in Git,
frontend, LLM context, logs, or plaintext DB. Rotated; access audited. Encryption key
in KMS; app-layer envelope for sensitive fields.

## 4. Encryption

- **In transit:** TLS everywhere; mTLS internal.
- **At rest:** RDS KMS; S3/KMS; field-level app encryption (email, phone, tokens, any
  sensitive).
- **Key rotation:** KMS key rotation; secrets rotation; agent credential rotation.

## 5. Network & edge

- CloudFront + WAF in front of the dashboard/API; AWS Shield for DDoS.
- ALB; services in private subnets; no direct internet to DB/Redis.
- SSRF protection on the LLM outbound proxy: allowlist hosts, block private/loopback/
  link-local/cloud metadata IP ranges, resolve-DNS-and-revalidate.

## 6. App-layer

- SQL injection: parameterized queries / ORM; no dynamic SQL from untrusted input; least
- privilege DB role (no `superuser`; app cannot DROP/traverse across tenants except via
  RLS).
- CSRF: SameSite cookies + CSRF tokens on dashboard mutation routes. CORS allowlisted.
- Rate limiting: Redis token bucket per API, per agent tool, per tenant.
- Input validation at every boundary; strict schema for agent/protocol payloads.

## 7. Webhook security

Verified signature, timestamp window, dedupe, idempotent application, DLQ. See `docs/14`.

## 8. Secret/credential handling rules

- No `secret` in logs; structured logging redacts known sensitive keys.
- Razorpay secret used only inside the Razorpay adapter; derived at runtime from the
  secrets layer; never stored in the app config/image.

## 9. CI/CD security

- Dependency scanning (own + transitives), secret scanning, container/image scanning,
  SAST, IaC scanning, signed artifacts, staged approvals. See `docs/23`.

## 10. Cloud controls

- IAM least privilege per service; no long-lived human access keys; audit logging via
  CloudTrail; S3 block public access; private endpoints for RDS/ElastiCache.

## 11. Cloud-agnostic minimums

The security model (authn/authz, RBAC+ABAC, secrets, encryption, rate limiting,
webhook verification, SSRF/SQLi/CSRF/CORS control, dependency scanning) is provider-
independent; only the control-plane implementation uses AWS services.
