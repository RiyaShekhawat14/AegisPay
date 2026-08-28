# 34 — Privacy

## 1. Data categories

| Category | Examples | Sensitivity |
|---|---|---|
| PII | email, phone, name, address | High (encrypted, minimized) |
| Payment data | provider order/payment refs, amount, currency | Medium (stored, not card data) |
| Merchant data | catalog, policies, campaigns | Local to tenant |
| Agent metadata | agent id, scopes, sessions | Low but principled (access audited) |
| Authorization | mandate terms, hashes | Sensitive (hashed/bound) |

AegisPay **never** stores card numbers/PAN or raw provider cards; only provider refs.

## 2. Data minimization

- Store only what is required (e.g., consent, amount, category, time, agent, provider ref).
- Favor hashes/opaque refs over raw PII; tokenize where possible.
- LLM/agent context receives no raw PII and only aggregated/minimized data.
- Don't collect device/IP unless needed for risk (and then redact/anonymize after use).

## 3. Encryption & redaction

- In transit: TLS; at rest: KMS + RDS/S3 encryption.
- Field-level encryption (email/phone/name) via app-layer envelope (KMS key).
- Logs/events: redact PII; store hashes. Risk: logs never show full emails/phones.

## 4. Access control & audit

- RLS + RBAC; scoped read/write; no broad access.
- Every access to sensitive data is auditable; agents cannot read PII beyond scoped,
  minimized needs.

## 5. Retention & deletion

- Retention per `docs/33`. PII pruned after deactivation tail; right-to-erase via a
  deletion job that redacts PII, keeps necessary audit evidence (anonymized, hashed),
  and records the deletion event.
- Hard-purging raw webhooks/export data per schedule.

## 6. Indian regulatory awareness (honest)

- AegisPay is designed with data minimization, user-rights awareness, consent, and
  security consistent with India's **DPDP Act** direction and RBI/payment
  requirements — but we **do not assert legal compliance** or claim certification.
- A qualified privacy/legal review is a **launch gate** (see `docs/36`). We also
  support data-subject access/deletion workflows for where they apply.
- We do not invent "RBI-approved", "DPDP-compliant", or "PCI-DSS-certified" claims.
  Card data is never handled (provider-hosted), which is a strong default; the exact
  PCI scope is to be confirmed with the provider and legal.

## 7. Principles

Minimize, encrypt, redact, retain-as-needed, control access, audit, honor erasure,
and state honestly what is/is not in scope.
