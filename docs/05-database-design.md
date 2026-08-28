# 05 — Database Design

> PostgreSQL 16+. Every table: `id BIGSERIAL PK`, `tenant_id BIGINT NOT NULL`, RLS
> policy, `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at`, optional `deleted_at`
> (soft delete) unless marked immutable. Money is stored as `BIGINT` **minor units**
> (paise/kobo). Tenant isolation via RLS (see §4). Secrets/tokens/locator data are
> field-level encrypted at the application layer. Full column dictionary in
> `docs/06-data-dictionary.md`.

## 1. Global conventions

- **Money:** `BIGINT` minor units; never `FLOAT`. Currency as `CHAR(3)`.
- **Hashes:** `CHAR(64)` hex (SHA-256) for integrity hashes; message digests for
  request/passport hashes. Salted where PII-bound.
- **Status fields:** `VARCHAR(32)` constrained sets; transition enforcement in app,
  plus `CHECK` constraints where a simple invariant holds.
- **Encryption:** high-sensitivity columns (`*_enc`, `*_token`) stored as `BYTEA`
  or `TEXT` ciphertext via AWS KMS envelope at the app layer; associated `kms_ref`.
- **Soft delete:** `deleted_at` on merchant-facing aggregates only. **Never** on:
  `payments`, `payment_attempts`, `audit_events`, `idempotency_keys`,
  `webhook_events`, `approval_decisions` — immutable/audit.
- **RLS enabled** on every tenant table; `audit_events` additionally **read-only**
  (no UPDATE/DELETE grant).

## 2. Tables, keys, constraints, indexes, encryption

### 2.1 merchants
- Columns: `id, tenant_id, name, slug UNIQUE, business_type, country, currency,
  status, default_autonomy_level, razorpay_key_id, kms_ref, created_at, updated_at, deleted_at`.
- PK `id`; FK none (top of tenant). Unique `(tenant_id, slug)`.
- `razorpay_key_id` is the public key id only. Index `(tenant_id, status)`.
- Soft delete: yes. Encryption: `razorpay_key_id` is a public id (not encrypted);
  the actual handle is in Secrets Manager.

### 2.2 merchant_users
- Columns: `id, tenant_id, user_id, email_enc, name, role, password_hash, oidc_sub,
  mfa_enabled, status, last_login_at, created_at, updated_at, deleted_at`.
- PK `id`; FK `tenant_id→merchants.tenant_id`. Unique `(tenant_id, user_id)`,
  `(tenant_id, email_enc)` (via CITEXT/deterministic hash).
- Index `(tenant_id, role)`. Encrypted: `email_enc`. Soft delete: yes.

### 2.3 agents
- Columns: `id, tenant_id, agent_key UNIQUE(tenant,key), owner_user_id, agent_type,
  version, scopes JSONB, allowed_tools JSONB, trust_level, status, expires_at,
  created_at, updated_at, deleted_at`.
- PK `id`; FK `owner_user_id→merchant_users`. Status ∈ `ACTIVE/SUSPENDED/REVOKED/EXPIRED`.
- Index `(tenant_id, status)`, `(tenant_id, agent_type)`. Unique `(tenant_id, agent_key)`.

### 2.4 agent_credentials
- Columns: `id, tenant_id, agent_id, name, credential_hash, credential_prefix,
  scopes JSONB, last_used_at, revoked_at, expires_at, created_at, updated_at`.
- PK `id`; FK `agent_id→agents`. Index `(agent_id, revoked_at)`. `credential_hash`
  only (never plaintext). Soft delete: no (immutable-ish; revoke instead).

### 2.5 agent_sessions
- Columns: `id, tenant_id, agent_id, session_key, ip, device, user_agent, started_at,
  ended_at, revoked_at, created_at`. Index `(agent_id, started_at)`. No soft delete.

### 2.6 customers
- Columns: `id, tenant_id, customer_ref, email_enc, phone_enc, name_enc, status,
  created_at, updated_at, deleted_at`.
- Unique `(tenant_id, customer_ref)`. Index `(tenant_id, email_hash)`. Encrypted:
  `email_enc, phone_enc, name_enc`. Soft delete: yes.

### 2.7 customer_authorizations (mandates)
- Columns: `id, tenant_id, customer_id, agent_id, version, scope, upper_value_minor,
  per_txn_minor, valid_from, valid_to, status, mandate_hash, created_at, updated_at, deleted_at`.
- FK `customer_id→customers`, `agent_id→agents`. Unique `(customer_id, agent_id, version)`.
- `mandate_hash` binds the terms (SHA-256 of normalized terms). Index `(customer_id, status)`.

### 2.8 mandates (stored authorization object)
- Columns: `id, tenant_id, customer_authorization_id, agent_id, terms JSONB, value_limit_minor,
  per_txn_minor, valid_from, valid_to, mandate_hash, status, signed_by, created_at, deleted_at`.
- One `mandate_hash` may be referenced by many transactions; the **binding** to a
  transaction is a separate one-time token (see `approval_requests`/passport).

### 2.9 products
- Columns: `id, tenant_id, catalog_id, sku UNIQUE(tenant,sku), name, name_indexed tsvector,
  description, category, price_minor, currency, status, allow_list BOOLEAN, block_list BOOLEAN,
  metadata JSONB, created_at, updated_at, deleted_at`.
- FK `catalog_id→catalogs`. Index `(tenant_id, category, status)`, GIN on `name_indexed`.
- Price is server-side authority. Soft delete: yes.

### 2.10 catalogs
- Columns: `id, tenant_id, name, slug, description, status, created_at, updated_at, deleted_at`.
- Unique `(tenant_id, slug)`. Soft delete: yes.

### 2.11 inventory
- Columns: `id, tenant_id, product_id, stock, version, reserved, updated_at, deleted_at`.
- FK `product_id→products`. `version` for optimistic locking. `CHECK (stock + reserved >= 0)`.
- Index `(product_id)`. Soft delete: yes.

### 2.12 carts
- Columns: `id, tenant_id, customer_id, agent_id, status, currency, cart_hash,
  expires_at, created_at, updated_at, deleted_at`.
- FK `customer_id, agent_id`. Unique `customer_id, agent_id`. Index `(tenant_id, status)`.
- `cart_hash` = SHA-256 of ordered, canonicalized `cart_items`. Soft delete: yes.

### 2.13 cart_items
- Columns: `id, tenant_id, cart_id, product_id, quantity, unit_price_minor, line_total_minor,
  hash_component, created_at, updated_at, deleted_at`.
- FK `cart_id, product_id`. Unique `(cart_id, product_id)`. `unit_price_minor` is
  server-copied from product/pricelist, never from client. `CHECK (quantity > 0)`.

### 2.14 commerce_intents
- Columns: `id, tenant_id, agent_id, user_id, kind, summary, raw_hash, intent_hash,
  intent_payload JSONB, status, expires_at, created_at, updated_at, deleted_at`.
- FK `agent_id, user_id`. `intent_hash` binds the structured proposal. Index `(tenant_id, status)`.

### 2.15 intent_items
- Columns: `id, tenant_id, intent_id, product_id OR product_snapshot JSONB, quantity,
  unit_price_minor, line_total_minor, hash_component, created_at`. FK `intent_id`.
- No soft delete (snapshot).

### 2.16 orders
- Columns: `id, tenant_id, cart_id, intent_id, customer_id, agent_id, currency,
  total_minor, status, policy_version, risk_score, authorization_id, created_at, updated_at, deleted_at`.
- FK `cart_id, intent_id, customer_id, agent_id, authorization_id`. Index
  `(tenant_id, status, created_at)`, `(agent_id)`, `(authorization_id)`.
- `policy_version` frozen at creation. Soft delete: yes (but never if a payment exists).

### 2.17 order_items
- Columns: `id, tenant_id, order_id, product_snapshot JSONB, product_id, quantity,
  unit_price_minor, line_total_minor, created_at`. FK `order_id`. **Immutable** — no
  update/delete grants normally; no soft delete.

### 2.18 payments
- Columns: `id, tenant_id, order_id, amount_minor, currency, provider, provider_payment_id,
  provider_order_id, capture_id, status, idempotency_key, attempt_count, unknown_since,
  created_at, updated_at`. FK `order_id`. Index `(order_id, status)`, `(provider, provider_payment_id)`,
  `(tenant_id, status)`. Unique `(idempotency_key)` where provider-scoped; global unique
  on the provider transaction id. **No soft delete.** `status` machine enforced.

### 2.19 payment_attempts
- Columns: `id, tenant_id, payment_id, attempt_no, provider_txn_id, request_hash,
  outcome, provider_response_hash, created_at`. FK `payment_id`. Index `(payment_id, attempt_no)`.
  **Append-only**, no soft delete.

### 2.20 refunds
- Columns: `id, tenant_id, payment_id, amount_minor, currency, reason, status,
  idempotency_key, provider_refund_id, created_at, updated_at`. FK `payment_id`.
- Unique/function guarantee: one effective refund per `(payment_id, idempotency_key)`;
  `CHECK (amount_minor <= captured amount)` enforced in app+trigger.
- Index `(payment_id, status)`. **No soft delete.**

### 2.21 policies
- Columns: `id, tenant_id, name, version VARCHAR, status, dsl TEXT, effective_at,
  supersedes_pointer, created_by, created_at, updated_at, deleted_at`.
- Unique `(tenant_id, name, version)`. Index `(tenant_id, status, effective_at)`.
- Immutable per version; a new row on change. Soft delete: no (retain history).

### 2.22 policy_versions
- Columns: `id, tenant_id, policy_id, version, dsl, checksum, published_at, retired_at,
  created_by`. FK `policy_id`. Unique `(policy_id, version)`. Append-only.

### 2.23 policy_rules
- Columns: `id, tenant_id, policy_id, rule_id, effect(ALLOW/DENY/REQUIRE_APPROVAL/REQUIRE_STEPUP),
  dimension, operator, value JSONB, precedence, not_before, enabled`. FK `policy_id`.
- Index `(policy_id, precedence)`. No soft delete.

### 2.24 risk_assessments
- Columns: `id, tenant_id, target_type, target_id, score, level(LOW/MEDIUM/HIGH/CRITICAL),
  factors JSONB, recommended_action, model_version, created_at`. Index `(tenant_id, target_type, target_id)`.
- Append-only; new assessment per evaluation.

### 2.25 approval_requests
- Columns: `id, tenant_id, order_id, agent_id, requester_user_id, scope_hash,
  require_approver_role, amount_minor, status, expires_at, decided_at, created_at, updated_at`.
- FK `order_id, agent_id`. Index `(tenant_id, status)`, `(order_id)`. Unique active per order.
- `scope_hash` binds the exact approved scope. No soft delete.

### 2.26 approval_decisions
- Columns: `id, tenant_id, approval_request_id, approver_user_id, decision(APPROVE/REJECT),
  reason, decision_hash, created_at`. FK `approval_request_id`. Unique
  `(approval_request_id)` (single decision). Index `(approver_user_id, created_at)`.
- **Append-only, no soft delete.** Reuse rejected by scope_hash + single-use.

### 2.27 campaigns
- Columns: `id, tenant_id, agent_id, name, budget_minor, spent_minor, status,
  targeting JSONB, discount_policy_ref, policy_version, risk_score, created_at, updated_at, deleted_at`.
- Index `(tenant_id, status)`. Unique `(tenant_id, name, version)`. Budget cap enforced.
- Soft delete: yes.

### 2.28 campaign_actions
- Columns: `id, tenant_id, campaign_id, kind(recommend/upsell/coupon), product_id_id,
  payload JSONB, order_id, created_at`. FK `campaign_id`. Index `(campaign_id)`. Append-only.

### 2.29 protocol_sessions
- Columns: `id, tenant_id, agent_id, protocol, external_session_id, authn_ref,
  scopes JSONB, started_at, ended_at, created_at`. Unique `(protocol, external_session_id)`.
- Maps external protocol session → canonical identity.

### 2.30 audit_events
- Columns: `id, tenant_id, event_type, actor, actor_type, correlation_id, causation_id,
  trace_id, payload JSONB, previous_hash, event_hash, event_signature, created_at`.
- Index `(tenant_id, event_type, created_at)`, `(correlation_id)`, `(event_hash)`.
- **Append-only; no UPDATE/DELETE grants; no soft delete.** Hash-chain integrity.

### 2.31 audit_event_hashes
- Columns: `id, tenant_id, anchor_ts, chain_start, chain_end, anchor_hash, anchored_to,
  created_at`. Periodic checkpoint pins to external root.

### 2.32 idempotency_keys
- Columns: `key, tenant_id, endpoint, request_hash, response, status, expires_at, created_at`.
- PK composite `(tenant_id, endpoint, key)`. Index `(tenant_id, endpoint, expires_at)`.
- Response replay cache with TTL. **No soft delete.**

### 2.33 webhook_events
- Columns: `id, tenant_id, provider, provider_event_id, event_type, payload_hash,
  raw_reference, signature_verified, status(RECEIVED/VERIFIED/DEDUPED/APPLIED/FAILED),
  received_at, created_at`. Unique `(provider, provider_event_id)`. Index `(provider, status)`.
- **No soft delete.** Raw payload in S3; reference stored.

### 2.34 webhook_deliveries
- Columns: `id, tenant_id, webhook_event_id, delivery_no, status, next_attempt_at,
  attempts, max_attempts, last_error, created_at`. FK `webhook_event_id`.
- Index `(webhook_event_id)`. No soft delete.

### 2.35 reconciliation_jobs
- Columns: `id, tenant_id, payment_id, job_no, status, next_attempt_at, attempts,
  max_attempts, result, escalated, created_at, updated_at`. FK `payment_id`.
- Index `(payment_id, status)`, `(next_attempt_at)`. No soft delete.

### 2.36 notifications
- Columns: `id, tenant_id, channel, recipient_ref, kind, payload JSONB, status,
  attempts, next_attempt_at, created_at`. Index `(tenant_id, status)`. Soft delete: no.

## 3. Cross-cutting constraints

- `commit` semantics double as the audit write: the audit event is written in the
  same transaction that mutates money/state, so you can never have a state change
  without an audit record.
- Unique constraints are the **last line of defense** (idempotency, single active
  approval, one refund per key, one decision per request).
- Read replicas: analytics only, RLS preserved; never used for the money path.

## 4. Row-Level Security

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY orders_ts ON orders
  USING (tenant_id = current_setting('app.tenant_id')::bigint)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::bigint);
-- repeated for every tenant table
```

Access resolver (middleware) executes `SET LOCAL app.tenant_id = :tenant` per
request on the transaction-scoped connection after validating the caller's tenancy.

## 5. Migration strategy

Forward-only expanding/contracting migrations with code-compatible two-phase
deploys. No destructive/shrinking DDL in one release; `git`-managed, tested,
reviewed. See `docs/23-ci-cd.md`.

## 6. Backup & retention

RDS automated backups + PITR (RPO ≤ 15 min), multi-AZ failover, WAL archiving, S3
cross-region copy aspirational. Retention: DB snapshots ≥ 7–35 days (configurable),
audit ledger ≥ 6 years (regulator-timeline adjustable, flagged as review), raw
webhooks ≥ 90 days. See `docs/33-data-retention.md`.
