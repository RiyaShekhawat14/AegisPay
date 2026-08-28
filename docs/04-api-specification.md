# 04 — API Specification (REST)

## 1. Conventions

- Base path `/v1`, JSON, ISO-8601 timestamps, `BIGINT` money in minor units.
- Auth: `Authorization: Bearer <token>` (OIDC users), `X-Api-Key` (scoped agent/merchant),
  mTLS internally.
- `Idempotency-Key` header on every mutating endpoint; server is idempotent + dedupes.
- Tenant resolved from auth (never from body). Standard error envelope (see
  `docs/30`); rate-limit headers `X-RateLimit-Limit/Remaining/Reset`.
- Full OpenAPI 3.1 in `api/openapi.yaml`.

## 2. Endpoints

### Merchants & agents
- `POST /v1/merchants` → create merchant; returns `merchant_id`.
- `POST /v1/agents` → register agent (key, scopes, allowed_tools, policy, trust).
- `POST /v1/agents/{id}/rotate-credentials`, `POST /v1/agents/{id}/suspend`.

### Catalog
- `POST /v1/catalogs`, `GET /v1/catalogs`, `POST /v1/catalog/products`,
  `POST /v1/catalog/products/{id}/index`.
- `GET /v1/catalog/products?q=&category=&page=` → list/search.
- `GET /v1/catalog/products/{id}` → product detail (agent-readable model).

### Intents & carts
- `POST /v1/intents` → compile agent output into a structured intent; returns
  `intent_id, intent_hash`.
- `POST /v1/carts`, `POST /v1/carts/{id}/items`, `DELETE /v1/carts/{id}/items/{itemId}`.
- `POST /v1/carts/{id}/checkout` → lock cart, compute hash, create order.
- `GET /v1/carts/{id}`.

### Authorization & approval
- `POST /v1/authorization/requests` → evaluate policy+risk; returns ALLOW /
  APPROVAL_REQUIRED / DENIED + `authorization_hash` when ALLOWED.
- `POST /v1/approvals/{id}/approve`, `POST /v1/approvals/{id}/reject` (scoped,
  expiring, single-use).

### Orders & payments
- `POST /v1/orders` → create order from locked cart+bound intent.
- `GET /v1/orders/{id}`, `POST /v1/payments`, `GET /v1/payments/{id}`.
- `POST /v1/payments/{id}/capture`, `POST /v1/payments/{id}/refund`.

### Webhooks
- `POST /v1/webhooks/razorpay` → verified signature, dedupe, process.

### Trust / audit
- `GET /v1/transactions/{id}/passport` → signed provenance bundle.
- `GET /v1/audit/events?correlation_id=&event_type=` → audit trail (tenant-scoped).

### Growth / campaigns
- `POST /v1/growth/opportunities` → discover opportunities (affinity).
- `POST /v1/campaigns`, `POST /v1/campaigns/{id}/execute`,
  `GET /v1/campaigns/{id}/analytics`.

## 3. Per-endpoint contract example (representative)

### `POST /v1/payments`
- **Auth:** API key (merchant/agent scope) or user token.
- **Authz:** must already have `authorization_hash` from `/authorization/requests`;
  fails if absent/invalid/expired (see error codes).
- **Request:**
```json
{ "order_id": "ord_1", "authorization_hash": "abc…", "method": "card" }
```
- **Response:** `200` → `{ "payment_id", "status": "PENDING|CAPTURED|UNKNOWN", "provider_order_id" }`
- **Validation:** order exists, authorization valid+unexpired, amount matches bound.
- **Errors:** `AUTHORIZATION_ERROR`, `APPROVAL_REQUIRED`, `POLICY_DENIED`,
  `RISK_BLOCKED`, `PROVIDER_ERROR`, `CONFLICT` (same key/diff request).
- **Idempotency:** `Idempotency-Key` required; replay returns the prior result.
- **Rate limit:** per agent key; **Audit:** `payment.initiated`.

## 4. Pagination

Cursor-based (`?cursor=…&limit=`); default 20, max 100. response: `next_cursor`.

## 5. Errors & rate-limiting headers

See `docs/30` for the catalogue. Uniform envelope:
```json
{ "code": "POLICY_DENIED", "message": "Amount exceeds transaction limit.",
  "request_id": "req_x", "retryable": false }
```

## 6. Security review of API

- All money endpoints require a valid authorization; no endpoint accepts a client-
  supplied price/status/tenant.
- Webhook is a separate, minimal-privilege path.
- Sensitive resources are tenant-scoped by auth → RLS, tested for isolation.
