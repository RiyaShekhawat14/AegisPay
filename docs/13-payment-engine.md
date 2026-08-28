# 13 — Payment Engine

## 1. Purpose

The payment engine is the **only** component allowed to instruct a provider to move
money. It owns payment lifecycle, provider abstraction, idempotent idempotency, and
state integrity. It never trusts the frontend, the agent, or a client-sent status.

## 2. Provider abstraction

```python
class PaymentProvider(Protocol):
    async def create_order(self, input: CreateOrderInput) -> ProviderOrder: ...
    async def fetch_order(self, order_ref: str) -> ProviderOrder: ...
    async def initiate_payment(self, input: InitPaymentInput) -> ProviderPayment: ...
    async def fetch_payment(self, payment_ref: str) -> ProviderPayment: ...
    async def capture(self, input: CaptureInput) -> ProviderPayment: ...      # where applicable
    async def refund(self, input: RefundInput) -> ProviderRefund: ...
    async def verify_webhook(self, event: RawEvent) -> VerifiedEvent: ...
    async def reconcile(self, order_ref: str, payment_ref: str) -> ProviderPayment: ...
```

Razorpay is an implementation (`docs/razorpay-integration` in payment-engine notes).
No `paid`, `order_id`, `udf`, `razorpay_*` concept escapes this package. The rest of
the codebase sees `PaymentStatus`, `ProviderOrderID`, `ProviderPaymentID`, `amount`.

## 3. Lifecycle

`createOrder → initiatePayment → (capture) → verify via webhook/reconcile → terminal`.

- **createOrder** — provider order with amount (minor units) + receipt. Idempotent:
  keyed by `order_id` (our key) + request hash.
- **initiatePayment** — bind provider payment to order. Idempotent by
  `payment_id`. Returns immediate provider verdict or `UNKNOWN`.
- **capture** — explicit, amount-bounded, only when expected (many providers auto-
  capture; Razorpay invoices/orders can be manual). Never auto-capture by default.
- **terminate** — only via **verified webhook** or **reconciliation result**. No
  client can set terminal state.

## 4. Idempotency (exact behavior)

Request → provider succeeds → network timeout → client retry:

```
POST /v1/payments  { Idempotency-Key: pk_abc }
  1. Key {pk_abc, /v1/payments} not found → proceed
  2. provider.InitiatePayment → provider returns payment_id, but network drops
  3. client retries with same Idempotency-Key
  4. Idempotency store has key with status=IN_PROGRESS idempotency + provider_payment_id
     → return SAME provider_payment_id (no second charge)
     OR if the request hash differs → CONFLICT (400), block
  5. A webhook/reconciliation later resolves the true status
```

Guarantee: unique constraint on `(tenant_id, endpoint, key)`. Replay returns the
stored response. A **different** request under the same key is rejected. Provider
refunds/captures are likewise idempotented by `(payment_id, idempotency_key)`.

## 5. State machine (summary)

`CREATED → AUTHORIZATION_PENDING → CAPTURE_PENDING → CAPTURED | FAILED`, with
`UNKNOWN` as a first-class state reachable from `CAPTURE_PENDING`/`AUTHORIZATION_PENDING`.
`UNKNOWN` exits **only** via verified webhook or reconciliation. See `docs/32`.

## 6. Failure modes

| Scenario | Behavior |
|---|---|
| Provider timeout | `UNKNOWN`; never blind-retry; reconcile |
| Provider 5xx | transient retry with backoff + circuit breaker; if still failing, `UNKNOWN` |
| Webhook not received | find via reconciliation after a grace period |
| Poison result | treated as `UNKNOWN`, escalate, never auto-apply |
| Client double-send | idempotency key returns prior result |

## 7. Security boundary

- Provider **secret keys** exist only in the secrets layer, resolved at the adapter
  boundary; logs/context never contain them.
- The payment engine is invoked **only** after authorization + policy + risk pass. It
  does no policy evaluation itself.
- Refund is amount-capped to captured and single-effective per key.

## 8. Observability & testing

Payment initiation/failure/capture latency, unknown rate, circuit state. Units: state
machine + idempotency. Integration: against Razorpay Test Mode (real create/capture/
fail/refund). Failure: timeout + replay + duplicate + out-of-order. All green before
any real money.

## 9. Why provider-agnostic

Razorpay is required now; other providers (or a future NPCI UP gateway) are
inevitable. Confining provider detail to one adapter keeps the money path auditable
and portable. Rejected: hard-coding Razorpay everywhere (would spread secrets + states,
hurt testability and future-proofing).
