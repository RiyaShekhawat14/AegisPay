# 45 — API Error Catalog

## 1. Envelope

```json
{
  "code": "PAYMENT_AUTHORIZATION_REQUIRED",
  "message": "Human approval is required before this payment can proceed.",
  "request_id": "req_01J…",
  "retryable": false,
  "correlation_id": "corr_…"
}
```

- `code` — stable machine code; `message` — human; `request_id` — trace; `retryable`
  — whether caller may re-submit the identical request.
- Error `message` never contains secrets/PII/stack traces.

## 2. Categories & codes

### VALIDATION_ERROR
- `VALIDATION_MISSING_FIELD`, `VALIDATION_INVALID_VALUE`, `VALIDATION_SCHEMA_MISMATCH`,
  `VALIDATION_PRICE_MISMATCH` (client price ≠ server price), `VALIDATION_INVALID_STATE`.
  (retryable=false)

### AUTHENTICATION_ERROR
- `AUTH_INVALID_TOKEN`, `AUTH_EXPIRED_TOKEN`, `AUTH_INVALID_API_KEY`,
  `AUTH_CREDENTIAL_REVOKED`. (retryable=false)

### AUTHORIZATION_ERROR
- `AUTHZ_NOT_AUTHORIZED`, `AUTHZ_EXPIRED`, `AUTHZ_SCOPE_MISMATCH`,
  `AUTHZ_CART_CHANGED`, `AUTHZ_BINDING_MISMATCH` (replay/substitution), 
  `AUTHZ_MANDATE_REVOKED`. (retryable=false)

### POLICY_DENIED
- `POLICY_TXN_LIMIT_EXCEEDED`, `POLICY_DAILY_LIMIT_EXCEEDED`,
  `POLICY_CATEGORY_BLOCKED`, `POLICY_HOURS_NOT_ALLOWED`, `POLICY_RESTRICTED_CATEGORY`,
  `POLICY_BLOCKED`. (retryable=false)

### RISK_BLOCKED
- `RISK_CRITICAL`, `RISK_LEVEL_HIGH`, `RISK_ENGINE_UNAVAILABLE`. (retryable=false,
  last one may be retryable=true after recovery)

### APPROVAL_REQUIRED
- `APPROVAL_REQUIRED`, `APPROVAL_EXPIRED`, `APPROVAL_ALREADY_USED`,
  `APPROVAL_SCOPE_MISMATCH`. (retryable=false)

### PAYMENT_ERROR
- `PAYMENT_UNKNOWN`, `PAYMENT_ALREADY_CAPTURED`, `PAYMENT_REFUND_AMOUNT_INVALID`,
  `PAYMENT_REFUND_EXCEEDS_CAPTURED`, `PAYMENT_CAPTURE_ALREADY`. (retryable=false)

### PROVIDER_ERROR
- `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`,
  `PROVIDER_INVALID_SIGNATURE`. (timeout/unavailable retryable=true)

### CONFLICT
- `IDEMPOTENCY_KEY_REUSED` (different request under same key), `STATE_CONFLICT`,
  `DUPLICATE_REQUEST`. (retryable=false)

### RATE_LIMITED
- `RATE_LIMITED` (with `Retry-After`). (retryable=true)

### INTERNAL_ERROR
- `INTERNAL_ERROR` (500), `DEPENDENCY_UNAVAILABLE`. (retryable=true conservatively,
  with a bounded policy)

## 3. Mapping to HTTP

| Envelope code family | HTTP |
|---|---|
| VALIDATION_ERROR | 400 |
| AUTHORIZATION_ERROR/AUTHN | 401/403 |
| POLICY_DENIED / RISK_BLOCKED | 403 |
| APPROVAL_REQUIRED | 409 (or 202 with a link) |
| PAYMENT_ERROR | 422 |
| PROVIDER_ERROR | 502/504 |
| CONFLICT | 409 |
| RATE_LIMITED | 429 |
| INTERNAL_ERROR | 500 |

## 4. Idempotency & retry semantics

- Idempotent endpoints honour `Idempotency-Key`. Replaying the **same** request
  returns the original response (200), even after success. A **different** payload
  under the same key → `IDEMPOTENCY_KEY_REUSED` (409).
- `retryable: true` implies the caller may retry **the identical key**; it never
  implies the server silently re-executed a financial action.
