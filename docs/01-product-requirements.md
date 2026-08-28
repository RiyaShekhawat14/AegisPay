# 01 — Product Requirements

## 1. Vision

AegisPay is the **control plane for agentic commerce** — the trust layer between AI
agents and financial infrastructure. It does not move money itself; it **authorizes,
policies, risks-scopes, human-gates, executes (via a provider), and audits** money.
Its defining guarantee: *no LLM can directly control money movement.*

## 2. Personas

| Persona | Goal |
|---|---|
| Merchant owner | Enable autonomous commerce with bounded risk; policies, approvals, visibility |
| Merchant risk/compliance | Control spending, set limits, review escalations, satisfy auditors |
| Shoppers / end users | Consent to an agent, cap spending, see and revoke authorizations |
| Business admin (MerchantOps) | Manage agents, catalogs, campaigns, API keys, security |
| Agent AI (agent provider) | Discover catalog, build carts, request authorization — within limits |
| Auditors / regulators | Full explainable, tamper-evident trail of every decision |

## 3. Core Problem

LLMs are probabilistic; payment APIs are deterministic; financial action requires
authorization, explainability, and safety. AI agents can be manipulated (prompt
injection, tool poisoning, cart tampering) and can be made to overstep. Merchants
need bounded autonomy, users need consent and visibility, and auditors need proof.

## 4. Goals

- G1. AI agents can discover products, build carts, and request payments.
- G2. Every financial action is gated by deterministic policy + risk + authz.
- G3. High-risk actions require human approval; nothing auto-executes outside policy.
- G4. Every money decision is explainable and auditable.
- G5. Provider failures produce uncertainty that is reconciled, never double-charged.
- G6. AegisPay works with Razorpay Test Mode out of the box.
- G7. Agentic protocols (MCP/A2A/x402) are pluggable without coupling core logic.

## 5. Functional Requirements

### 5.1 Merchants & Catalog
- FR-101 Create/manage merchant; merchant has a razorpay key id (never a raw secret).
- FR-102 Manage users, roles (RBAC: admin, ops, policy_admin, analyst, approver).
- FR-103 Manage catalogs; products have server-side price (minor units), category,
  allow/block controls.
- FR-104 Product data is treated as **untrusted** for injection defenses.

### 5.2 Agents
- FR-201 Register/manage agents: key, scopes, allowed tools, policy, trust level,
  expiry, status (ACTIVE/SUSPENDED/REVOKED/EXPIRED).
- FR-202 Agent cannot modify its own policy or scopes.
- FR-203 Rotate/revoke agent credentials.

### 5.3 Intent, Cart, Order
- FR-301 Agent can search catalog, read product, compare products.
- FR-302 Compile LLM output into a structured, hashable `CommerceIntent`.
- FR-303 Create/modify cart; server-authoritative prices; lock at checkout; hash.
- FR-304 Create order from a locked cart+bound intent; order items are frozen.
- FR-305 Every order carries policy_version and risk_score.

### 5.4 Authorization
- FR-401 User/agent mandate grants bounded spending authority (scope, value limits,
  validity).
- FR-402 Request authorization for an intent+cart; bind to a transaction digest.
- FR-403 Authorization is transaction-bounded, single-use, expiry-checked, hashed.

### 5.5 Policy & Risk
- FR-501 Deterministic policy engine returns ALLOW/DENY/HUMAN_APPROVAL_REQUIRED/
  STEP_UP_AUTHENTICATION.
- FR-502 Versioned, immutable policies; rollback via pointer move.
- FR-503 Explainable risk score + factors + recommended action + model_version.
- FR-504 LLM is never the final risk authority.

### 5.6 Human-in-the-Loop
- FR-601 Escalate to approval inbox with scope hash + expiry + role.
- FR-602 Approve/reject with reason; decision is single-use and non-stale.

### 5.7 Payments & Providers
- FR-701 Provider-abstracted lifecycle (createOrder, initiate, capture, refund,
  fetch, verify, reconcile).
- FR-702 Razorpay adapter implemented; Test Mode first.
- FR-703 Capture explicit amount-bounded; refund idempotent & amount-capped.

### 5.8 Webhooks & Reconciliation
- FR-801 Verify signature, timestamp, dedup, persist raw, apply idempotently.
- FR-802 Resolve UNKNOWN state via reconciliation with backoff; never blind retry.

### 5.9 Audit & Passport
- FR-901 Append-only hash-chained audit ledger for every financial event.
- FR-902 Transaction Passport exposes signed provenance for any transaction.

### 5.10 Growth Agent
- FR-1001 Recommendations/campaigns that still flow through policy/risk/approval;
  budget and discount caps.

### 5.11 Protocols
- FR-1101 Adapters for MCP, A2A, and best-effort x402 over a Canonical Commerce Model.

## 6. Non-Functional Requirements

| NFR | Requirement | Target |
|---|---|---|
| Security | LLM cannot move money; secrets never reach LLM/logs | Enforced by code + tests |
| Reliability | Fail closed on financial authz; provider/DB/queue failures safe | Documented + chaos-tested |
| Availability | Single-region multi-AZ | ~99.9% phase 1, honest |
| Performance | policy p95 <50ms; risk p95 <100ms; init capture p95 <2s | Profiled |
| Scalability | Multitenant; stateless control-plane horizontal | Shared-schema RLS |
| Auditability | Every financial event recorded | Append-only + chain |
| Privacy | Minimization + encryption + retention | Field-level encryption |
| Compliance | India DPDP-aware (no legal claims) | Review gate |

## 7. Scope Boundaries

**In:** policy/risk/authz/approval, provider abstraction, webhooks, reconciliation,
Transaction Passport, audit ledger, protocol adapters, growth agent, dashboards.

**Out (v1):** wallet, cards, direct NPCI, multi-currency settlement, lending, PSP
licensing claims, real-money settlement.

## 8. Acceptance Criteria (Phase 1)

MUST before any real-value payment capability:

1. No money action executes without a valid, non-stale passport + policy ALLOW.
2. Duplicate financial action is structurally impossible (idempotency + state).
3. Provider timeout → UNKNOWN → reconciliation; no double charge.
4. Prompt-injected agent cannot authorize payment (red-team green).
5. Every financial decision has a retrievable, verifiable passport.
6. Tenant isolation proven by cross-tenant access tests.
7. Secrets absent from logs, code, and LLM context.
