# ADR-010 — Protocol abstraction

## Context
MCP/A2A/ACP/AP2/x402 and future UAP are evolving. Coupling the core to any one is a bet
on an unproven standard; the money path must not change when standards do.

## Problem
Support emerging agent protocols without coupling the core, and without claiming
compliance we can't verify.

## Options
1. **Protocol Gateway + Canonical Commerce Model** — adapters normalize into a canonical
   model; core never imports a protocol SDK.
2. Hard-code a chosen protocol as the core contract, or extend the core per protocol.

## Decision
**Adapter layer over a Canonical Commerce Model.** The core sees only the canonical
intent/cart/authorization; protocol adapters are optional transports.

## Rationale
- Isolates churn; easy to add/remove protocols.
- Protects Invariant 12: adapters cannot bypass the trust layer (they always resolve to
  the deterministic pipeline).
- Honest posture: "supports/adapts", never claims compliance.

## Trade-offs
Translation overhead + adapter code. Hidden cost if a protocol becomes dominant (we
still map it).

## Consequences
`protocol_sessions` map external identities to canonical `agent_id`; new protocols are
new adapters only.
