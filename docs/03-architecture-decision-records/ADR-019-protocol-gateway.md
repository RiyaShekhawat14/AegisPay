# ADR-019 — Protocol Gateway implementation

## Context
AegisPay must accept many agentic-commerce protocols (MCP, A2A, ACP, UCP, AP2, x402, and
future NPCI UAP/UPI) without coupling the core to any one protocol, and without letting
any protocol create a new money path.

## Problem
One entry point that authenticates, validates, protects against replay, enforces
idempotency, and normalizes every protocol into the single intent the control plane
understands.

## Options
1. **Protocol Gateway over a Canonical Intent** (chosen) — each protocol has an adapter
   that maps its message to a `CanonicalIntent`; the core never imports a protocol SDK.
2. Protocol-specific endpoints inline with a per-protocol concern in the core.

## Decision
A `protocol_gateway` module with:
- `canonical.py` — the `CanonicalIntent` contract and an allowlist/forbid-list of actions.
  Money actions (`EXECUTE_PAYMENT`, `ISSUE_REFUND`, `MODIFY_ORDER`, `UPDATE_POLICY`) are
  **forbidden** from any adapter by construction.
- `adapters.py` — one adapter per protocol (`A2A`, `MCP`, `ACP`, `UCP`, `AP2`, `x402`,
  `UPI`), each mapping to a non-money canonical action.
- `gateway.py` — `enter()` applies **authenticate → schema-validate → replay-protect →
  idempotency → normalize → validate**, and never yields a payment action.

## Rationale
- One contract for the control plane; a new protocol is a new adapter, not a new money path.
- The gateway is the single choke point for authn, schema, replay and idempotency.
- Honest: the gateway is **implemented and unit-tested** as pure logic. Live protocol
  wire-ups (accepting real MCP/A2A HTTP/JSON-RPC frames, DB-backed idempotency store,
  per-tenant authentication) are **wiring pending** and are not claimed as complete.

## Trade-offs
A thin mapping layer per protocol (code). Benefit: isolation + honest, bounded churn.

## Consequences
`app/modules/protocol_gateway/`; unit tests `tests/unit/test_protocol_gateway.py` verify
normalization, replay/idempotency, and that **no adapter can produce a payment action**.
