# 41 — Agent Commerce Protocols: Deep Analysis

> **Honesty rule:** this file distinguishes (1) official standardized capabilities,
> (2) experimental capabilities, (3) our internal abstractions, (4) future
> compatibility. AegisPay makes **no claim of compliance** with any protocol. Where we
> say "supports/adapts", that is true of our adapter; where we say "future
> compatibility", that is a plan, not a fact. Where a protocol's public detail is
> thin, we say so.

## 1. Maturity table

| Protocol | Owner | Maturity | Primary purpose | AegisPay posture |
|---|---|---|---|---|
| MCP | Anthropic (open) | Production-ish, widely used | Tool/resource/prompt access for LLM apps | `SUPPORT` — MCP server exposing safe tools |
| A2A | Google (open) | Early but real | Agent-to-agent task/message interop | `SUPPORT` — A2A agent endpoint |
| ACP | IBM-led | Early/concurrent | Agent-to-agent interaction (JsonRPC, messages) | `ADAPT` — map to canonical model |
| AP2 | Google | Experimental | Agent payments (close commerce processor loop) | `MAP-LATER` — where semantics align |
| x402 | Coinbase | Experimental | HTTP-payment-based access to resources/models | `MAP-LATER` — where semantics align |
| NPCI UAP | NPCI (India) | Preliminary / little public detail | Agentic payments in India (UPI-adjacent) | `WATCH` — no claims; future compatibility |
| UCP / UPI ecosystem concepts | Various | Not finalized | Commerce/identity interoperability | `WATCH` — no claims |

## 2. Canonical Commerce Model (our internal abstraction)

Every adapter maps to one internal canonical model so the core never imports a
protocol SDK:

```text
Protocol Adapter (MCP/A2A/ACP/AP2/x402)
        ↓  normalized
Canonical Commerce Model
        ↓
AegisPay Core (intent → policy → risk → authorization → payment → audit)
```

The canonical model is a typed contract (`agent_id`, `merchant_id`, `protocol`,
`session`, `action`, `cart`, `intent`, `authorization`, `provider`) — see
`docs/18-protocol-integration.md`.

## 3. Per-protocol analysis

### MCP (Model Context Protocol)
- **What it handles:** exposing tools, resources, and prompts to an LLM client. JSON-
  RPC 2.0 over stdio (local) or streamable HTTP (remote); authorization via OAuth 2.1.
- **Where it fits in AegisPay:** an **MCP server** advertises safe tools
  (`search_catalog`, `get_product`, `add_to_cart`, `calculate_total`,
  `request_authorization`, …). Dangerous capabilities (`execute_payment`,
  `issue_refund`, `modify_order`) are **never** exposed as MCP tools.
- **AegisPay adapter:** validates incoming tool calls against the allowlist, binds
  the MCP session to a canonical `agent_id`, and routes through the intent compiler.
- **Trade-off:** MCP is tool-level, great for agent→AegisPay, but it is not a
  payment/commerce protocol. It does not itself define the money path — which is
  exactly why AegisPay must own the money path and only expose safe tools.

### A2A (Agent2Agent)
- **What it handles:** agent-to-agent interaction via `AgentCard` discovery, tasks,
  message-level exchanges. Lets another agent request a task (e.g., "find and buy
  running shoes").
- **Where it fits:** an **A2A agent endpoint** for a merchant's storefront agent or an
  AI buyer. The external agent sends an A2A task; AegisPay normalizes it into the
  canonical model and the same PROTECT pipeline runs.
- **AegisPay adapter:** authenticate the remote agent (OAuth/OIDC), map `AgentCard`
  capabilities to allowed operations, ensure every task resolves to an intent that
  passes policy/risk/authorization.
- **Trade-off:** A2A is richer than MCP for multi-agent flows but the security model
  depends on each agent being correctly authenticated & scoped. AegisPay treats the
  remote agent as an untrusted *caller*, not a trusted peer.

### ACP (Agent Communication Protocol)
- **What it handles:** conversational/structured agent interaction (messages, cards)
  over JSON-RPC; concurrent with A2A and overlapping in goal.
- **Where it fits:** as an **adapter** to the canonical model, not a native integration.
- **Trade-off:** overlapping standards mean we should not build the core around any
  one. An adapter keeps us portable and avoids coupling to one winner.

### AP2 (Agent Payments Protocol)
- **What it handles (public/early):** intended to let agents complete payments by
  "closing the loop" with a commerce processor, with a wallet/session and
  settlement. Experimental; spec is being defined.
- **AegisPay stance:** **do not claim support now.** Where its *semantics* (a session,
  an authorization amount, a settlement) map to our canonical intent/authorization,
  we can map it — but as a *future* adapter behind policy+risk+authz. AegisPay
  deliberately does not let any external payment protocol bypass its control plane.

### x402
- **What it handles (public/experimental):** an "HTTP 402" style protocol where access
  to a resource/model requires a payment (Coinbase), typically with stablecoin
  settlement and a payment token.
- **Where it fits:** not a *merchant commerce* protocol primarily; it is about
  *paying to consume a resource*. Where it intersects AegisPay is if an agent needs to
  pay *for* a resource — that is a payment to invoke, which can be routed through our
  payment engine as a normal provider-funded action. Treat as future interoperability.

### NPCI UAP (Unified Agent Protocol) — India
- **Current public status:** NPCI has been engaging with agentic commerce generally
  (UPI-adjacent); a specific "Unified Agent Protocol" with a public, stabilized spec
  is **not established in a form we can assert compliance to**. Treat this as
  **emerging and unconfirmed**.
- **AegisPay stance:** no claim. We keep the provider abstraction and protocol gateway
  flexible so that *if* a UAP/agentic-payment standard materializes, it can be added
  as an adapter without touching core. Document as **future compatibility / watch**.
- **Assumption vs fact:** the design *assumes* a generic "agentic payment in India may
  ride on UPI rails"; we do **not** assert NPCI approval, an API surface, or a
  compliance claim. The Razorpay adapter (and future provider adapters) is the seam
  where such rails would plug in.

### UCP / other commerce-identity concepts
- Not finalized and overlapping. Tracked; no claims. AegisPay's provider + protocol
  abstraction is the hedge.

## 4. Design consequence

The core (policy, risk, authz, payment, audit, passport) is **protocol-agnostic**. New
protocols are new adapters over the canonical model. This is Invariant 12: **protocol
adapters cannot bypass the AegisPay trust layer** — every protocol path collapses into
the same deterministic pipeline.

## 5. What we never do

- We never claim "MCP-compliant/A2A-compliant/x402-compliant" as a certification.
- We never let a protocol introduce a payment path that bypasses policy/risk/authz.
- We never treat a remote agent or a protocol payload as trusted.
- We never store protocol secrets in the core; adapters authenticate but the money
  credentials stay in the secrets layer.
