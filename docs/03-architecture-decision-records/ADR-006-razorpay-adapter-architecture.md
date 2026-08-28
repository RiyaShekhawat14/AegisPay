# ADR-006 — Razorpay adapter architecture

## Context
Razorpay is the launch provider. Future providers (or NPCI-era rails) are likely. The
core must not know Razorpay semantics (order ids, udfs, webhook fields, keys).

## Problem
Integrate Razorpay without leaking vendor concepts, secrets, or states into the core.

## Options
1. **Provider interface + adapter** — canonical model everywhere; adapter maps to/from.
2. Hard-code Razorpay across modules — simple initially, but a tangled, secret-carrying
   codebase.

## Decision
**Provider interface (`PaymentProvider`) + Razorpay adapter**, isolated in
`internal/providers/razorpay`.

## Rationale
- Portability: swap providers without touching policy/risk/order/audit.
- Security: the Razorpay secret is read only at the adapter boundary; never in logs/LLM.
- Testability: a fake provider drives unit/state tests; Test Mode drives integration.

## Trade-offs
One extra mapping layer (canonical↔provider). Confined, so cheap.

## Consequences
Core sees `PaymentStatus`, `ProviderOrderID`, `ProviderPaymentID`, `amount` — no Razorpay
concept crosses the boundary. Webhook verification is adapter-owned.
