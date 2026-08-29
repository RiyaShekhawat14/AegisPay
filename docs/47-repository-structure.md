# 47 — Production Repository Structure

A single **monorepo** for the whole platform. Two runnable services (Control Plane,
AI Runtime), a web console, SQL migrations, tests and docs — kept together so
one change, one CI pipeline, and one history is easy to reason about. Deployment is
**local-first** via Docker Compose; a production AWS deployment is documented in
`docs/21-*` and added when an AWS account is available.

```
aegispay/
├── README.md                 # entry point & index of the docs
├── CONTRIBUTING.md           # how to change / regenerate docs & diagrams
├── .github/workflows/        # ci.yml (compile backend, validate OpenAPI/docs) — GitHub-hosted, no AWS needed
├── api/openapi.yaml          # OpenAPI 3.1 contract (shared by backend + web)
├── docs/                     # the engineering documentation set (00…54 + ADRs)
│   └── pdf/                  # the final published documents (architecture, GROW/SELL, frontend, schema)
├── pdf/                      # diagram/PDF generators + frontend mockup sources
│
├── api/                  # ⟵ ALL SERVER CODE (single service, two deploy units)
│   ├── pyproject.toml        # Python deps + ruff + pytest config
│   ├── .env.example          # every env var, no real secrets
│   ├── compose.yaml          # local dev: postgres(16) + redis + localstack(sqs) + services
│   ├── Makefile              # up / migrate / test / lint / run
│   ├── Dockerfile            # control-plane image
│   ├── Dockerfile.ai         # AI-runtime image (no DB, no secrets, no money tools)
│   ├── app/                  # CONTROL PLANE (FastAPI) — layered
│   │   ├── main.py           # app factory; mounts middleware, error handlers, v1 router
│   │   ├── api/
│   │   │   ├── deps.py       # auth + tenant + db-session + rate-limit dependencies
│   │   │   └── v1/router.py  # controllers (health, me, then carts/orders/payments…)
│   │   ├── middleware/       # request_id, tenant_context, rate_limit (+ contextvars for logs)
│   │   ├── core/             # config, security, jwt, authorization(RBAC+ABAC),
│   │   │                     #   ratelimit, exceptions, logging, db(SET LOCAL), rls
│   │   ├── db/               # (Phase 2) base, session, repositories (tenant-scoped)
│   │   ├── schemas/          # pydantic DTOs (common, auth, + per-resource)
│   │   ├── modules/          # commerce(+safety,flow), catalog, policy, risk, authorization,
│   │   │                     #   approvals, protocol_gateway, idempotency, payments,
│   │   │                     #   webhooks, reconciliation, refunds, campaigns, opportunities,
│   │   │                     #   audit, passport, outbox, events
│   │   ├── workers/          # webhook processor, reconciliation, outbox relay
│   │   └── schemas/          # pydantic DTOs
│   ├── ai_runtime/           # ISOLATED AI RUNTIME (FastAPI) — no DB, no secrets, no money tools
│   │   ├── main.py           # /internal/intent/compile only
│   │   ├── agents/           # sell agent, grow agent (LangGraph)
│   │   ├── graph/            # langgraph state, nodes, edges, checkpointer
│   │   ├── tools/            # allowlisted safe tools (dangerous tools never here)
│   │   ├── prompts/          # templates (kept as data, never a security boundary)
│   │   └── schemas.py        # typed CommerceIntent
│   ├── migrations/0001_init.sql  # v1 schema + RLS + tenant-prefixed indexes
│   └── tests/                # conftest, unit, integration, e2e, redteam
│
└── frontend/                      # ⟵ FRONTEND (Next.js + TypeScript + Tailwind)
    ├── package.json / tsconfig.json / next.config.mjs / tailwind.config.ts
    └── src/
        ├── app/              # layout, pages (dashboard, catalog, agents, campaigns, approvals…)
        ├── components/       # shared UI (design tokens from tailwind.config)
        ├── lib/              # api client + generated types
        └── types/
```

## Why this shape

| Choice | Why |
|---|---|
| **Monorepo** | One change, one CI, one history; cross-cutting contracts (OpenAPI, migrations, shared types) stay in sync. |
| **Two services, not more** | Control Plane owns money; AI Runtime is isolated by privilege. Extracting more microservices early adds distributed-transaction pain for no benefit. |
| **Modular monolith** (`app/modules/`) | Clear boundaries so modules can be lifted into services later without a rewrite. |
| **Migrations + RLS in SQL** | Schema truth lives in versioned SQL; RLS is enforced by the DB, not just app code. |
| **`frontend/src/lib` from OpenAPI** | The frontend contract is generated from the same OpenAPI, so client and server never drift. |
| **Local-first deployment** | Docker Compose runs the stack (Postgres 16 + Redis + Localstack SQS) with no cloud account; AWS infra is documented in `docs/21-*` and added when needed. |
| **Docs co-located** | The architecture set and ADRs live with the code so engineers and reviewers read one artifact. |

## Not included (deliberately)

- No per-protocol payment systems, no separate auth microservice, no Kafka, no
  Kubernetes, no blockchain, no event-store database, no separate policy/risk services,
  and **no Terraform/AWS IaC** (added only when an AWS account exists) —
  these would add complexity without proving safety at this scale.
