# AegisPay — Full Folder Structure

`
.
├── .github/
│   └── workflows/
│       ├── api-ci.yml
│       ├── integration.yml
│       └── web-ci.yml
├── .vscode/
│   └── extensions.json
├── api/
│   ├── ai_runtime/
│   │   ├── agents/
│   │   │   └── __init__.py
│   │   ├── graph/
│   │   │   └── __init__.py
│   │   ├── prompts/
│   │   │   └── __init__.py
│   │   ├── tools/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── config/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── authorization.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── exceptions.py
│   │   ├── jwt.py
│   │   ├── logging.py
│   │   ├── observability.py
│   │   ├── ratelimit.py
│   │   ├── rls.py
│   │   └── security.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── init.sql
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── session.py
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── db.py
│   ├── graph/
│   │   ├── nodes/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── middleware.py
│   ├── modules/
│   │   ├── approvals/
│   │   │   └── __init__.py
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   └── ledger.py
│   │   ├── authorization/
│   │   │   └── __init__.py
│   │   ├── campaigns/
│   │   │   ├── __init__.py
│   │   │   └── budget.py
│   │   ├── catalog/
│   │   │   └── __init__.py
│   │   ├── commerce/
│   │   │   ├── __init__.py
│   │   │   ├── flow.py
│   │   │   └── safety.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   └── envelope.py
│   │   ├── idempotency/
│   │   │   ├── __init__.py
│   │   │   └── service.py
│   │   ├── opportunities/
│   │   │   └── __init__.py
│   │   ├── outbox/
│   │   │   ├── __init__.py
│   │   │   └── relay.py
│   │   ├── passport/
│   │   │   ├── __init__.py
│   │   │   └── service.py
│   │   ├── payments/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   └── state.py
│   │   ├── protocol_gateway/
│   │   │   ├── __init__.py
│   │   │   ├── adapters.py
│   │   │   ├── canonical.py
│   │   │   └── gateway.py
│   │   ├── reconciliation/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── refunds/
│   │   │   └── guard.py
│   │   ├── risk/
│   │   │   └── __init__.py
│   │   ├── webhooks/
│   │   │   ├── __init__.py
│   │   │   └── processor.py
│   │   └── __init__.py
│   ├── policy/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── repositories/
│   │   └── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── router.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── common.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── payments.py
│   │   ├── razorpay.py
│   │   └── razorpay_mock.py
│   ├── tests/
│   │   ├── e2e/
│   │   │   └── __init__.py
│   │   ├── fixtures/
│   │   │   └── __init__.py
│   │   ├── integration/
│   │   │   └── test_health.py
│   │   ├── redteam/
│   │   │   └── __init__.py
│   │   ├── unit/
│   │   │   ├── test_authorization.py
│   │   │   ├── test_budget.py
│   │   │   ├── test_commerce_safety.py
│   │   │   ├── test_idempotency.py
│   │   │   ├── test_jwt.py
│   │   │   ├── test_payment_state.py
│   │   │   ├── test_policy.py
│   │   │   ├── test_protocol_gateway.py
│   │   │   ├── test_purchase_flow.py
│   │   │   ├── test_ratelimit.py
│   │   │   └── test_refund_guard.py
│   │   └── conftest.py
│   ├── websockets/
│   │   └── __init__.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── outbox_relay.py
│   │   ├── reconciliation_worker.py
│   │   └── webhook_processor.py
│   ├── .dockerignore
│   ├── .env.example
│   ├── __init__.py
│   ├── Dockerfile
│   ├── Dockerfile.ai
│   ├── main.py
│   ├── Makefile
│   ├── pyproject.toml
│   └── README.md
├── db/
│   ├── migrations/
│   │   └── 0001_initial.sql
│   ├── seeds/
│   │   └── dev_products.sql
│   └── README.md
├── deploy/
│   ├── compose/
│   │   ├── docker-compose.dev.yml
│   │   ├── docker-compose.test.yml
│   │   └── docker-compose.yml
│   └── docker/
│       └── nginx.conf
├── docs/
│   ├── 03-architecture-decision-records/
│   │   ├── ADR-001-go-vs-node.md
│   │   ├── ADR-002-modular-monolith-vs-microservices.md
│   │   ├── ADR-003-postgresql-architecture.md
│   │   ├── ADR-004-redis-usage.md
│   │   ├── ADR-005-queue-technology.md
│   │   ├── ADR-006-razorpay-adapter-architecture.md
│   │   ├── ADR-007-policy-engine-architecture.md
│   │   ├── ADR-008-risk-engine-architecture.md
│   │   ├── ADR-009-llm-isolation.md
│   │   ├── ADR-010-protocol-abstraction.md
│   │   ├── ADR-011-audit-ledger.md
│   │   ├── ADR-012-transaction-passport.md
│   │   ├── ADR-013-secrets-management.md
│   │   ├── ADR-014-multi-tenancy.md
│   │   ├── ADR-015-authentication.md
│   │   ├── ADR-016-deployment-architecture.md
│   │   ├── ADR-017-global-kill-switch.md
│   │   ├── ADR-018-transactional-outbox.md
│   │   └── ADR-019-protocol-gateway.md
│   ├── openapi/
│   │   └── openapi.yaml
│   ├── pdf/
│   │   ├── AegisPay-Agentic-Commerce-Architecture-V4.pdf
│   │   ├── AegisPay-Architecture-V3.pdf
│   │   ├── AegisPay-Database-Schema.pdf
│   │   ├── AegisPay-Frontend-GROW.pdf
│   │   ├── AegisPay-Frontend-SELL.pdf
│   │   ├── AegisPay-LangGraph-GROW-V3.pdf
│   │   └── AegisPay-LangGraph-SELL-V3.pdf
│   ├── 00-architecture-master.md
│   ├── 00b-grow-sell-protect.md
│   ├── 01-product-requirements.md
│   ├── 02-system-architecture.md
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
│   ├── 27-agent-readable-catalog.md
│   ├── 28-growth-agent.md
│   ├── 29-campaign-orchestrator.md
│   ├── 30-merchant-autonomy.md
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
│   ├── 41-protocols.md
│   ├── 42-incident-response.md
│   ├── 43-runbook.md
│   ├── 44-security-runbook.md
│   ├── 45-api-error-catalog.md
│   ├── 47-repository-structure.md
│   ├── 49-engineering-phases.md
│   ├── 54-success-metrics.md
│   ├── AI_JUDGMENT.md
│   ├── API_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT_LOG.md
│   ├── GUARDRAILS_AND_SAFETY.md
│   ├── PRD.md
│   └── SCHEMA.sql
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── Badge.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── index.ts
│   │   │   ├── Input.tsx
│   │   │   └── StatusDot.tsx
│   │   └── lib/
│   │       └── api.ts
│   ├── .env.example
│   ├── next.config.mjs
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── pdf/
│   ├── _html/
│   │   ├── aegispay_live_flow.html
│   │   ├── grow_frontend.html
│   │   └── sell_frontend.html
│   ├── build_db.py
│   ├── build_db_easy.py
│   ├── build_db_simple.py
│   ├── build_langgraph.py
│   ├── build_pdf.py
│   ├── build_v2.py
│   ├── build_v3.py
│   └── build_v4.py
├── scripts/
│   ├── ci/
│   │   └── run-integration.sh
│   └── dev/
│       ├── bootstrap.ps1
│       └── bootstrap.sh
├── tests/
│   └── e2e/
│       ├── specs/
│       │   └── checkout-flow.spec.ts
│       └── playwright.config.ts
├── workers/
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── hold_expiry.py
│   │   └── reconciliation.py
│   ├── __init__.py
│   ├── config.py
│   ├── Dockerfile
│   ├── main.py
│   ├── pyproject.toml
│   ├── reconciliation.py
│   └── webhook_processor.py
├── .gitignore
├── CONTRIBUTING.md
├── Makefile
├── README.md
└── STRUCTURE.md
`
