# 19 — MCP / A2A Integration

## 1. Goal

Expose AegisPay's safe capabilities to AI agents/LLM runtimes over standard agent
protocols (MCP and A2A, with other protocols as adapters — see `docs/18` and
`docs/41`) **without** exposing the money path or coupling the core.

## 2. Layering

```
Agent/LLM (MCP client OR A2A peer)
   ↓                          ↓
MCP Server (tools)        A2A Agent Endpoint (tasks)
   └──────────┬───────────────┘
   Protocol Gateway (normalize) → Canonical Commerce Model → AegisPay Core
```

## 3. MCP server

- **Exposes:** MCP **tools** (the safe set) and MCP **resources/prompts** for catalog
  discovery. Tools are read/aggregate actions plus intent/cart/authorization requests.
- **Never exposes:** payment execution, refund, policy/budget mutation. Dangerous
  capabilities are simply not advertised, so a capable-but-scoped MCP client cannot
  invoke them.
- **Auth:** OAuth 2.1 client credentials / authorization, mapped to the canonical
  `agent_id`. Each session → `protocol_sessions` binding.
- **Session mgmt:** MCP session → internal agent session with TTL, scope, revocation.

## 4. A2A agent endpoint

- **Exposes:** an A2A `AgentCard`, `Task` handling, message/artifact exchange.
- A remote agent (AI buyer, merchant storefront agent) sends a task ("find and buy
  running shoes under ₹4,000"). AegisPay normalizes it and runs intent → policy → risk
  → authz → (approval) → payment → webhook/reconcile → passport.
- **Auth:** OAuth/OIDC for the remote agent/subject; the remote peer is treated as an
  **untrusted caller**, not a trusted peer. Its `AgentCard` capabilities are mapped to
  allowed operations (never a grant of financial authority).

## 5. Canonical Agent Identity (internal)

The canonical identity is the single authority across protocols:

```
AgentID:      out of the canonical store (agents table)
Owner:        merchant_user
Type:         AI_BUYER | GROWTH | STOREFRONT | MARKETPLACE
Version:      semver of the agent
Credential:   hashed, scoped API key / OIDC subject (mapped from protocol auth)
Scopes:       allowlisted
AllowedTools: the safe tool set for this agent
Policy:       the effective policy (from merchant/agent config)
TrustLevel:   HIGH/MEDIUM/LOW
Expiration:   never-forever; rotatable
Status:       ACTIVE/SUSPENDED/REVOKED/EXPIRED
```

Mapping: MCP/OAuth/A2A/OIDC subjects all resolve to an `agent_id`; a `protocol_sessions`
row records which protocol session maps to which canonical identity. This prevents
identity confusion across protocols (an A2A "agent" is not silently the same as an MCP
"agent" unless explicitly linked).

## 6. Capability discovery & honesty

- Advertised capabilities = the safe tool set + read-only catalog resource. We never
  claim dangerous capabilities exist.
- `agent.json` / `AgentCard` capabilities are generated from the canonical scopes, so a
  peer cannot "discover" a capability we don't grant.

## 7. What every protocol path resolves to

Regardless of protocol, the destination is the same: an intent that must pass policy →
risk → authorization → (approval) → payment → audit → passport. A protocol adapter is
only a transport; it cannot skip PROTECT. (Invariant 12.)

## 8. Errors & semantics

- Protocol-level errors are translated to the standard AegisPay error envelope with
  `retryable`, `request_id`, etc., so the agent can act on a typed failure.

## 9. Security notes

- Adapters authenticate but never possess the money credentials.
- Session/context isolation per agent; no cross-agent context bleeding.
- All adapter calls are rate-limited, budget-bound, and audited.
