# AegisPay

> **The Trust & Growth Layer for Agentic Commerce**

**AI can reason. AegisPay controls whether it is allowed to act.**

AegisPay is an agentic-commerce **control plane** that delivers three pillars:

# GROW
Help merchants increase revenue with AI (upsell, cross-sell, bundles, campaigns,
segment/re-engagement).

# SELL
Make merchants discoverable and transactable by AI buyers (agent-readable catalog,
discovery, conversational checkout, end-to-end transaction).

# PROTECT
Ensure every AI-driven financial action is explainable, bounded, gated, authorized,
auditable, idempotent and recoverable (policy, risk, authorization, human-in-the-loop,
Transaction Passport, audit, reconciliation, prompt-injection defense).

The architectural consequence of GROW+SELL+PROTECT is one invariant:

> **AI may propose a financial action. Only the deterministic AegisPay control
> plane may authorize and execute it.**

```
AI Reasoning
     ↓
Structured Intent
     ↓
Intent Validation
     ↓
Policy Evaluation
     ↓
Risk Evaluation
     ↓
Authorization
     ↓
Human Approval if Required
     ↓
Payment Execution
```

No LLM ever receives secret keys, database credentials, unrestricted payment/refund
APIs, or the authority to move money directly. **`LLM → Razorpay` is impossible by
construction.**

---

## Why this repository exists

This is the **engineering documentation set** for AegisPay, produced at production
depth. It is designed to be reviewed as if a **Razorpay engineer** is deciding whether
to approve it for production financial infrastructure — not as a hackathon scaffold.
It is honest about protocol maturity, avoids invented compliance claims, prefers
boring reliable infrastructure, and is built to graduate from **Razorpay Test Mode** to
production.

The defining result:

> Correctness, security, reliability and explainability are enforced by deterministic,
> versioned, auditable code paths — not by prompt engineering, not by model good
> behavior, not by hope. **AI can grow and sell. AegisPay makes money safe to let it.**

---

## Repository layout

```
AgeisPay/
├── README.md                              ← you are here (index)
├── docs/
│   ├── 00-architecture-master.md          ← THE master doc (full §59 ordering)
│   ├── 00b-grow-sell-protect.md           ← product model & challenge interpretation
│   ├── 01-product-requirements.md
│   ├── 02-system-architecture.md
│   ├── 03-architecture-decision-records/  ← ADR-001 … ADR-018
│   ├── 04-api-specification.md
│   ├── 05-database-design.md
│   ├── 06-data-dictionary.md
│   ├── 07-security-architecture.md
│   ├── 08-threat-model.md
│   ├── 09-agent-security.md
│   ├── 10-policy-engine.md
│   ├── 11-risk-engine.md
│   ├── 12-authorization-model.md
│   ├── 13-payment-engine.md
│   ├── 14-webhook-architecture.md
│   ├── 15-reconciliation.md
│   ├── 16-audit-ledger.md
│   ├── 17-transaction-passport.md
│   ├── 18-protocol-integration.md
│   ├── 19-mcp-a2a-integration.md
│   ├── 20-observability.md
│   ├── 21-infrastructure.md
│   ├── 22-deployment.md
│   ├── 23-ci-cd.md
│   ├── 24-testing-strategy.md
│   ├── 25-load-testing.md
│   ├── 26-disaster-recovery.md
│   ├── 27-agent-readable-catalog.md       ← SELL: machine-readable catalog (DATA vs INSTRUCTIONS)
│   ├── 28-growth-agent.md                 ← GROW: merchant revenue agent
│   ├── 29-campaign-orchestrator.md        ← GROW: campaign pipelines
│   ├── 30-merchant-autonomy.md            ← autonomy levels L0–L4
│   ├── 31-event-catalog.md
│   ├── 32-state-machines.md
│   ├── 33-data-retention.md
│   ├── 34-privacy.md
│   ├── 35-risk-register.md
│   ├── 36-production-readiness-checklist.md
│   ├── 37-threat-scenarios.md
│   ├── 38-red-team-plan.md
│   ├── 39-demo-script.md
│   ├── 40-engineering-roadmap.md
│   ├── 41-protocols.md                    ← deep per-protocol analysis (MCP/A2A/ACP/AP2/x402/UAP)
│   └── 54-success-metrics.md              ← measurable growth/safety/ops metrics
└── api/
    └── openapi.yaml                       ← OpenAPI 3.1 conformance
```

---

## How to read this

| You are… | Start with |
|---|---|
| Reviewer who needs the shortest path | `docs/00-architecture-master.md` |
| Strategy / product reviewer | `docs/00b-grow-sell-protect.md` |
| Payments engineer | `docs/13-*`, `docs/14-*`, `docs/15-*` |
| Policy/risk/authorization engineer | `docs/10-*`, `docs/11-*`, `docs/12-*`, `docs/17-*` |
| Agent/LLM security engineer | `docs/07-*`, `docs/09-*`, `docs/38-*` |
| Growth/campaign engineer | `docs/27-*`, `docs/28-*`, `docs/29-*`, `docs/30-*` |
| Protocol engineer | `docs/18-*`, `docs/19-*`, `docs/41-*` |
| Platform/infra engineer | `docs/21-*` → `docs/23-*` → `docs/26-*` |
| Hostile reviewer | `docs/36-*`, `00-architecture-master.md §50` |

---

## The non-negotiable production invariants

1. **No LLM ever executes a financial API directly.**
2. **Every financial action passes deterministic authorization + policy.**
3. **Unknown payment state is never blindly retried.** Unknown ⇒ reconcile.
4. **Every payment action is idempotent.**
5. **Material cart changes invalidate authorization.**
6. **Agents cannot modify their own permissions.**
7. **Human approvals are scoped, expiring, and non-replayable.**
8. **Webhooks are untrusted external events until verified.**
9. **Cross-tenant data access is impossible through normal application paths.**
10. **Every financial decision has an auditable explanation.**
11. **AI can grow and sell merchant revenue without unrestricted financial autonomy.**
12. **Protocol adapters cannot bypass the AegisPay trust layer.**

---

## Status

`DESIGN` — architecture and engineering documentation complete; no application code
yet. See `docs/40-engineering-roadmap.md` for the build sequence.
