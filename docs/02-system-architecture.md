# 02 — System Architecture

## 1. System boundaries

AegisPay has two external roles: **agents/LLMs** (upstream, proposing actions) and
**payment providers** (downstream, moving money). AegisPay is the opaque seam between
them: agents can only *propose*, providers only ever receive *authorized* work.

### 1.1 Trust boundaries (in order of increasing trust)

```
T1  Untrusted:  LLM/agent output + external protocol payloads + webhooks + catalog data
T2  Validated:  Compiled intents, normalized catalog, typed tool calls
T3  Controlled: Policy + risk + authorization decisions
T4  Authorized: Wallet-executable commands (createOrder/capture/refund)
T5  System:     Control-plane state, secrets, audit ledger
```

Each boundary is an explicit component (validators, compilers, guards, adapters),
not a hop.

## 2. High-level components

| Layer | Component | Deploy unit | Lang | Trust |
|---|---|---|---|---|
| Client | Merchant dashboard (Next.js/TS/Tailwind) | Web | TS | T0 |
| Client | Agent runtime, A2A/MCP clients | External | — | T0 |
| Access | Protocol Gateway + MCP/A2A/x402 adapters | Control plane | Python/FastAPI | T1 |
| Reasoning | LLM runtime, intent compiler | AI runtime | Python/FastAPI | T1→T2 |
| Control | Commerce Orchestrator, Policy, Risk, Authz, HITL, Payment, Webhook, Reconcile, Audit | Control plane | Python/FastAPI | T3/T4/T5 |
| Data | PostgreSQL (RLS), Redis, Queue, S3 | Managed | — | T5 |
| External | Razorpay Test APIs, LLM provider, notifications | — | — | T0 |

## 3. Control plane module decomposition (modular monolith)

Single FastAPI application; modules communicate through internal Python packages and one
domain event bus. Module boundaries:

```
control_plane/
  app/          → FastAPI router wiring, auth middleware, tenant context
  authn/        → OIDC/API-key/service-identity; tenant context resolution
  idemp/        → Idempotency guard
  intent/       → IntentCompiler (validated structured intent)
  catalog/      → Product/catalog read model + search
  cart/         → Cart aggregate + hash
  order/        → Order aggregate + state machine
  policy/       → Policy engine + DSL + versioning
  risk/         → Risk engine fusion
  authorize/    → Authorization engine (passport)
  approval/     → Human-in-the-loop
  payment/      → Payment engine + provider interface
  providers/razorpay/ → Adapter
  webhook/      → Gateway + processor
  reconcile/    → Reconciliation worker
  audit/        → Append-only ledger writer + verifier
  events/       → Domain event bus + envelope
  tools/        → Agent tool definitions (safe set)
  notify/       → Approval/escalation notifications
  analytics/    → Rollup/reporting
```

`ai_runtime/` is a separate FastAPI service (see ADR-009) — same language, different
permission/process boundary.

## 4. Async vs sync

- **Sync request path:** authn → tenant context → intent/cart validation → policy →
  risk → authorization issue → order/payment initiation → (if HITL) create request &
  return `APPROVAL_REQUIRED`.
- **Async worker path (queue):** webhook application, reconciliation, refund,
  notification, analytics rollup, campaign execution.

The sync path never awaits a provider webhook. Payment initiation returns the
provider's immediate result or `UNKNOWN`; truth is resolved asynchronously.

## 5. Communication contracts

| Route | Type | Contract |
|---|---|---|
| Agent → AegisPay | Sync | Protocol (MCP/A2A) → Intent API |
| AI runtime → control plane | Sync, mTLS | `POST /internal/intent/compile` |
| Control plane → provider | Sync + async | `PaymentProvider` interface, timeout 1, cursor-reconcile |
| Control plane → queue | Async | Durable, at-least-once, DLQ |
| Webhook gateway → queue | Async | Verified raw event |
| Audit → ledger | Sync (same tx) | Append-only within the action tx |

## 6. Multi-zone & horizontal scaling

- Stateless API pods behind ALB; lock/rate in Redis; queue in SQS.
- Workers as a separate task set, scaled by queue depth.
- Reads through RLS-enforced replica for analytics; writes to primary.

## 7. Security posture summary

- No secret to any Agent/LLM/protocol layer.
- Database access only from control plane; never from AI runtime.
- Webhook path is zero-trust (verify, dedupe, persist, apply idempotently).
- Fail-closed on policy/risk/authz/approval unavailability.

## 8. Failure philosophy

- **Money:** provider truth only; UNKNOWN reconciles; no blind retry; disable on
  doubt.
- **Decision:** if policy/risk unavailable → deny/escalate.
- **External:** every client has timeout + retry + circuit breaker + backoff.
- **Availability vs correctness:** AegisPay trades availability for correctness on
  the money path; the design is degraded-but-safe, not always-up-and-risky.
- **Coordinated stop:** a global emergency kill switch halts all new AI-initiated
  money movement (payments, refunds, campaign spend) while leaving reconciliation and
  audit active. Fail-closed: if the switch can't be read, no new money action proceeds.
- **Events:** every state change is written to a transactional outbox in the same
  transaction, then relayed to the queue — no lost or phantom events, and every change
  is automatically audited.

## 9. Operational model

One control plane deploy (API + workers) in one AWS region, multi-AZ. AI runtime a
second small service. Dashboards served from `next` static assets through
CloudFront; CORS restricted; WAF in front.
