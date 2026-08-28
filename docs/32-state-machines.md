# 32 — State Machines

Every aggregate has a single, guarded state machine. Transition functions are pure,
unit-tested, and reject illegal edges. **Payment state is never inferred from the
frontend, the agent, or the order state.**

## 1. Intent

```
CREATED ──> VALIDATED ──> AUTHORIZED ──> EXPIRED(SLIME)  *terminal*
   │            │             │
   │            ├────> REJECTED          *terminal*
   └──────────> EXPIRED         *terminal*
```

Legal edges:
- `CREATED → VALIDATED` after structured validation.
- `VALIDATED → AUTHORIZED` only if policy result is ALLOW or (approval granted).
- `VALIDATED → REJECTED` on policy DENY / invalid.
- `CREATED|VALIDATED → EXPIRED` on TTL.

Illegal: `AUTHORIZED → VALIDATED` (no backtrack), any transition out of a terminal
state.

## 2. Cart

```
CREATED ──> MODIFIED ──> LOCKED ──> CHECKOUT_READY ──> EXPIRED
  │              │                             │
  └────────────> EXPIRED                      └──> (consumed by Order)
```

- `LOCKED` freezes `cart_hash`; any post-lock item/price/quantity change requires
  unlocking (reset to MODIFIED) and recomputes the hash — a hash mismatch at
  checkout is a hard error, not a silent recompute.
- `CHECKOUT_READY` is entered only with a valid, non-empty locked cart whose
  server-side total equals the computed sum.

Illegal: `MODIFIED` after `LOCKED` without unlock; `CHECKOUT_READY` from `CREATED`.

## 3. Order

```
CREATED
   │
   ├─> AUTHORIZATION_PENDING ──> APPROVED ──> PAYMENT_PENDING ──> PAID ──> COMPLETED
   │            │                    │             │
   │            └─> REJECTED        │             └─> FAILED
   │                                └─> REJECTED
   └──> CANCELLED
PAID ──> REFUND_PENDING ──> REFUNDED
```

Notes:
- `PAID` requires a provider-verified payment success (webhook/reconciliation), never
  an optimistic local write.
- `PAYMENT_PENDING → FAILED` only on authoritative failure; an unknown/ambiguous
  provider result keeps the order in `PAYMENT_PENDING` (or a sub-state) and routes to
  reconciliation rather than failing.
- `REFUND_PENDING → REFUNDED` only after provider confirms refund.

## 4. Payment (independent)

```
CREATED ──> AUTHORIZATION_PENDING ──> CAPTURE_PENDING ──> CAPTURED (SUCCESS)  *terminal*
   │                 │                    │                    │
   │                 └──> FAILED         └──> UNKNOWN          └──> (drives Order>PAID)
   └──> FAILED                                    │
                                                 ├─webhook/recon─> CAPTURED or FAILED
                                                 └──> RECONCILIATION_PENDING
```

- `UNKNOWN` is a **first-class, sticky state**. It exits only via a **verified
  webhook** or a **reconciliation lookup** returning authoritatively `CAPTURED` or
  `FAILED`. A blind client retry is a no-op (idempotency + state guard).
- `CAPTURE_PENDING → CAPTURED` sets a `provider_capture_id`; capture is amount-bounded
  and requested lazily only when the authz allows (avoid auto-capture risk).
- `SUCCESS/CAPTURED` and `FAILED` are terminal; no reverse transitions.

## 5. Refund

```
CREATED ──> PENDING ──> PROCESSED ──> COMPLETED  *terminal*
   │           │            │
   └─> REJECTED            └─> FAILED
```

- Idempotent per `(payment_id, idempotency_key)`.
- Amount ≤ captured refundable; single effective refund per key.

## 6. Guard contract

Each transition function receives the aggregate, the intent (passport/request hash),
and the caller context, and returns a typed result or an `IllegalTransition` error.
The guard performs: state-table check, passport validity + expiry, scope-hash match,
idempotency key check, and (for payment) provider verdict.

## 7. Design rules

1. No transition may be reachable without an authorized caller.
2. Terminal states are permanent; re-entry requires a new aggregate.
3. All transitions emit an event (== audit event).
4. Order and Payment states are decoupled — an order can be `PAYMENT_PENDING` while
   its payment is `UNKNOWN`; they reconcile independently.
