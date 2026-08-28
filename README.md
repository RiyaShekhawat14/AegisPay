# AegisPay

![CI](https://github.com/RiyaShekhawat14/AegisPay/actions/workflows/ci.yml/badge.svg)

> **The Trust &amp; Growth Layer for Agentic Commerce**

**AI can reason and recommend. Only AegisPay's deterministic control plane can authorize
and execute financial actions.**

AegisPay is a **control plane** between AI agents and payment infrastructure (Razorpay
today, other providers later). It is not a chatbot with a payment API attached — it is a
controlled financial execution system with an AI interface. This repository is the
engineering documentation set for that system, built to be reviewed as production
financial infrastructure, not a hackathon scaffold.

---

## The three pillars

| Pillar | What it does |
|---|---|
| **GROW** | AI helps merchants increase revenue: upsell, cross-sell, bundles, campaigns, A/B experimentation. Bounded and budget-controlled. |
| **SELL** | AI buyers understand intent, discover products, recommend, build carts, get authorization, and pay end-to-end through Razorpay. |
| **PROTECT** | AI can reason and recommend, but never directly controls money. Every AI money action is gated, explainable, auditable and recoverable. |

The architectural consequence of GROW + SELL + PROTECT is one invariant:

> **AI may propose a financial action. Only the deterministic AegisPay control plane may
> authorize and execute it.**

```
AI Reasoning → Structured Intent → Intent Validation → Policy → Risk → Authorization
            → Human Approval (if required) → Payment Execution → Webhook → Reconciliation → Audit
```

The AI runtime **never** receives secret keys, database credentials, unrestricted
payment/refund APIs, or the authority to move money. Money movement is impossible from
the AI layer by construction.

---

## Why this exists

AI agents are increasingly able to discover products and make purchasing decisions. But
LLMs are probabilistic and can be manipulated (prompt injection, tool poisoning, cart
tampering); payment APIs are deterministic and must be authorized, audited and safe to
recover from failure. AegisPay puts a **deterministic, versioned, auditable control plane**
between the two.

The defining property: **correctness, security, reliability and explainability are
enforced by code paths and versioned policies, not by prompt engineering or model good
behavior.** AI can grow and sell; AegisPay keeps the money safe while it does.

---

## System overview

```
 AI / Agent layer (proposes only)
   SELL agent          GROW agent
          \               /
           Structured intent
                    |
   AegisPay Control Plane (validates, authorizes, controls)
     Commerce Orchestrator · Policy · Risk · Authorization
     Payment Engine · Human Approval · Reconciliation · Audit + Passport
                    |
       Postgres (state + RLS + audit + outbox) · Redis · SQS
                    |
                 Razorpay
              (Verified webhook → Reconciliation → Transaction Passport)
```

There are exactly **two services**: the **Control Plane** (owns financial state, policy,
authorization, provider interaction, audit, reconciliation) and an **isolated AI Runtime**
(no database credentials, no payment secrets, no money tools, tool allowlist, structured
output, checkpointing).

---

## Repository layout

```
AgeisPay/
├── README.md                       ← you are here
├── CONTRIBUTING.md                 ← how to change and regenerate docs
├── .github/workflows/ci.yml        ← validation (OpenAPI, docs, build scripts)
├── api/
│   └── openapi.yaml                ← OpenAPI 3.1 contract
├── docs/                           ← engineering documentation set
│   ├── 00-architecture-master.md   ← the master architecture doc
│   ├── 00b-grow-sell-protect.md    ← product model
│   ├── 01-product-requirements.md  →  54-success-metrics.md
│   └── 03-architecture-decision-records/  ← ADR-001 … ADR-018
├── pdf/
│   ├── build_*.py                  ← PDF generators (mermaid + reportlab)
│   └── _html/*.html                ← frontend & live-flow mockup sources
└── AegisPay-*.pdf                  ← the final documents (see below)
```

### Final documents

| Document | Covers |
|---|---|
| `AegisPay-Agentic-Commerce-Architecture-V4.pdf` | The full production architecture, now protocol-aware (single Protocol Gateway → adapters → normalized intent → control plane) |
| `AegisPay-Architecture-V3.pdf` | The production architecture, now protocol-aware (Protocol Gateway, maturity tiers, protocol security) + outbox, payment state machine, webhook security, idempotency, refunds, atomic budget, A/B, threat model, SLOs, failure testing |
| `AegisPay-LangGraph-GROW-V3.pdf` | The merchant revenue agent flow |
| `AegisPay-LangGraph-SELL-V3.pdf` | The AI-buyer checkout flow |
| `AegisPay-Frontend-GROW.pdf` | The merchant console UI |
| `AegisPay-Frontend-SELL.pdf` | The AI-buyer checkout UI |
| `AegisPay-Database-Schema.pdf` | The simple, secure, multi-tenant PostgreSQL schema |

---

## How to read this

| You are… | Start with |
|---|---|
| Reviewer with the shortest path | `docs/00-architecture-master.md` |
| Product / strategy | `docs/00b-grow-sell-protect.md` |
| Payments engineer | `docs/13-*`, `docs/14-*`, `docs/15-*` |
| Policy / risk / authorization | `docs/10-*`, `docs/11-*`, `docs/12-*`, `docs/17-*` |
| Agent / LLM security | `docs/07-*`, `docs/09-*`, `docs/38-*` |
| Growth / campaigns | `docs/27-*`, `docs/28-*`, `docs/29-*`, `docs/30-*` |
| Protocol engineer | `docs/18-*`, `docs/19-*`, `docs/41-*` |
| Platform / infra | `docs/21-*` → `docs/23-*` → `docs/26-*` |
| Hostile reviewer | `docs/36-*`, `docs/00-architecture-master.md` |

---

## Technology

- **Backend** — Python / FastAPI (control plane + isolated AI runtime)
- **AI orchestration** — LangGraph (proposal layer, human-in-the-loop checkpoints)
- **Database** — PostgreSQL 16 (shared, RLS multi-tenant, JSONB, outbox, audit)
- **Cache / locks / rate** — Redis (never the source of truth)
- **Queue** — SQS (at-least-once, idempotent consumers, DLQ)
- **Frontend** — Next.js + TypeScript + TailwindCSS
- **Deployment** — AWS: CloudFront + WAF → ALB → ECS (Fargate); RDS, ElastiCache, SQS, S3, Secrets Manager + KMS, OpenTelemetry/CloudWatch
- **Protocols** — adapter layer over a canonical commerce model (MCP, A2A, ACP, AP2, x402, future UAP) — support/adapt, never unsupported compliance claims

---

## Non-negotiable invariants

1. No LLM ever executes a financial API directly.
2. Every financial action passes deterministic authorization + policy.
3. Unknown payment state is never blindly retried — unknown ⇒ reconcile.
4. Every payment action is idempotent.
5. Material cart changes invalidate authorization.
6. Agents cannot modify their own permissions.
7. Human approvals are scoped, expiring, and non-replayable.
8. Webhooks are untrusted external events until verified.
9. Cross-tenant data access is impossible through normal application paths.
10. Every financial decision has an auditable explanation.
11. AI can grow and sell merchant revenue without unrestricted financial autonomy.
12. Protocol adapters cannot bypass the AegisPay trust layer.

---

## Status

`DESIGN` — architecture and engineering documentation complete. No application code yet;
see `docs/40-engineering-roadmap.md` for the build sequence. Everything here follows
production engineering principles and is built to graduate from Razorpay Test Mode to
production.
