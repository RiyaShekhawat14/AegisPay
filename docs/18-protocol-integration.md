# 18 — Protocol Integration (Gateway + Canonical Model)

## 1. Purpose

AegisPay must support emerging agentic-commerce protocols (MCP, A2A, ACP, AP2, x402,
and future NPCI UAP/agentic-payment rails) **without** coupling the core to any single
protocol or standard. The core is protocol-agnostic; adapters are optional skins.

## 2. Structure

```
ACP ─────┐
AP2 ─────┤
MCP ─────┤
A2A ─────┤
x402 ────┤
UAP* ────┤        (future / watch)
          ↓
    Protocol Gateway
          ↓
    Canonical Commerce Model
          ↓
      AegisPay Core (policy/risk/authz/payment/audit)
```

## 3. Protocol Gateway responsibilities

- Dispatcher: route by protocol + capability.
- Authenticate: OAuth/OIDC / client creds / per-protocol identity → canonical agent.
- Normalize: map protocol-specific messages (tool call, task, message, payment
  request) into the canonical model.
- Validate: enforce scopes, allowlists, rate limits before touching core.
- Map out: translate core responses/errors back to the protocol.
- Session: `protocol_sessions` mapping to canonical identity + scope + TTL.

## 4. Canonical Commerce Model (the seam)

A typed, protocol-independent representation of a commerce action:

```
CanonicalCommerceAction {
  protocol: string
  agent_id: AgentID
  merchant_id, customer_id
  action: DISCOVER | RECOMMEND | ADD_TO_CART | CHECKOUT | REQUEST_AUTH | ...
  payload: { product_ref?, quantity?, amount_minor?, currency?, query? }
}
```

The core receives **only** the canonical model via an internal authenticated API. It
never sees a raw MCP/A2A/x402 payload.

## 5. Trade-offs & why

- **Why adapters:** protocols are young and may win/lose. Hard-coding a protocol (or
  worse, a payment protocol into the core) risks rewriting the core when a standard
  changes.
- **Cost:** an adapter layer adds a translation step (latency, code). Value is
  isolation + portability. We accept the small cost.
- **Rejected:** choosing one "official" protocol as the core contract — that couples us
  to an unproven winner and can't be verified as compliant anyway.

## 6. Honesty on compliance

See `docs/41`. AegisPay **claims support/adaptation**, not compliance. The adapter
layer is the hedge: whatever standard becomes real, we add a transport without
touching the money path. We explicitly do **not** claim NFC NPCI/UAP compliance because
its public spec is not stable enough to build against.

## 7. Security boundary (Invariant 12)

- Protocol adapters **cannot** introduce a payment path that bypasses policy/risk/authz.
- Adapters never hold money/secrets.
- Every adapter call that could lead to money resolves to the same deterministic
  pipeline; an adapter is never treated as a trusted peer.

## 8. Where protocols fit (one-line)

| Protocol | Fits as | AegisPay role |
|---|---|---|
| MCP | agent→AegisPay (tools) | expose safe tools |
| A2A | agent↔agent (tasks) | merchant/AI-buyer endpoint |
| ACP | agent↔agent (messages) | alternate adapter |
| AP2 | agent payments | future mapping |
| x402 | pay-to-access | future mapping |
| UAP* | India agentic payments | watch/future |

## Implementation status (honest)

A `protocol_gateway` module is implemented and unit-tested as pure logic (ADR-019):
- `canonical.py` — `CanonicalIntent` with a forbid-list; no adapter may yield a money action.
- `adapters.py` — `A2A`, `MCP`, `ACP`, `UCP`, `AP2`, `x402`, `UPI` → canonical actions.
- `gateway.py` — `enter()` applies authenticate → schema-validate → replay-protect →
  idempotency → normalize → validate.

**Implemented:** normalization, replay protection, idempotency, and the guarantee that no
protocol produces a payment execution (verified by `tests/unit/test_protocol_gateway.py`).

**Not yet implemented (wiring pending):** live protocol transport (real MCP/A2A HTTP and
JSON-RPC frames), an in-DB idempotency store, and per-tenant protocol authentication. These
are adapter-ready at the API boundary, not claimed as complete.