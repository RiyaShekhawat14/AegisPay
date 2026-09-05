# AegisPay — Full Folder Structure

```
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
│   │   ├── agents/__init__.py
│   │   ├── graph/__init__.py
│   │   ├── prompts/__init__.py
│   │   ├── tools/__init__.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── config/__init__.py
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
│   │   ├── nodes/__init__.py
│   │   └── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── middleware.py
│   ├── modules/
│   │   ├── approvals/__init__.py
│   │   ├── audit/{__init__.py, ledger.py}
│   │   ├── authorization/__init__.py
│   │   ├── campaigns/{__init__.py, budget.py}
│   │   ├── catalog/__init__.py
│   │   ├── commerce/{__init__.py, flow.py, safety.py}
│   │   ├── events/{__init__.py, envelope.py}
│   │   ├── idempotency/{__init__.py, service.py}
│   │   ├── opportunities/__init__.py
│   │   ├── outbox/{__init__.py, relay.py}
│   │   ├── passport/{__init__.py, service.py}
│   │   ├── payments/{__init__.py, provider.py, state.py}
│   │   ├── protocol_gateway/{__init__.py, adapters.py, canonical.py, gateway.py}
│   │   ├── reconciliation/{__init__.py, worker.py}
│   │   ├── refunds/{__init__.py, guard.py}
│   │   ├── risk/__init__.py
│   │   ├── webhooks/{__init__.py, processor.py}
│   │   └── __init__.py
│   ├── policy/{__init__.py, engine.py}
│   ├── repositories/__init__.py
│   ├── routers/{__init__.py, health.py, router.py}
│   ├── schemas/{__init__.py, common.py}
│   ├── services/{__init__.py, payments.py, razorpay.py, razorpay_mock.py}
│   ├── tests/
│   │   ├── e2e/__init__.py
│   │   ├── fixtures/__init__.py
│   │   ├── integration/test_health.py
│   │   ├── redteam/__init__.py
│   │   ├── unit/test_authorization.py
│   │   ├── unit/test_budget.py
│   │   ├── unit/test_commerce_safety.py
│   │   ├── unit/test_idempotency.py
│   │   ├── unit/test_jwt.py
│   │   ├── unit/test_payment_state.py
│   │   ├── unit/test_policy.py
│   │   ├── unit/test_protocol_gateway.py
│   │   ├── unit/test_purchase_flow.py
│   │   ├── unit/test_ratelimit.py
│   │   ├── unit/test_refund_guard.py
│   │   └── conftest.py
│   ├── websockets/__init__.py
│   ├── workers/{__init__.py, outbox_relay.py, reconciliation_worker.py, webhook_processor.py}
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
│   ├── migrations/0001_initial.sql
│   ├── migrations/0002_password_reset.sql
│   └── README.md
├── deploy/
│   ├── compose/{docker-compose.yml, docker-compose.dev.yml, docker-compose.test.yml}
│   └── docker/nginx.conf
├── docs/
│   ├── 03-architecture-decision-records/  ADR-001 … ADR-019
│   ├── openapi/openapi.yaml
│   ├── pdf/AegisPay-*.pdf  (7 final documents)
│   ├── 00-architecture-master.md … 54-success-metrics.md
│   ├── 47-repository-structure.md · 49-engineering-phases.md
│   ├── PRD.md · ARCHITECTURE.md · API_SPEC.md · AI_JUDGMENT.md
│   ├── GUARDRAILS_AND_SAFETY.md · DEVELOPMENT_LOG.md · SCHEMA.sql
├── frontend/
│   ├── src/app/{globals.css, layout.tsx, page.tsx}
│   ├── src/components/{Badge, Button, Card, DataTable, Input, StatusDot, index}.tsx
│   ├── src/lib/api.ts
│   ├── .env.example · next.config.mjs · package.json · tailwind.config.ts · tsconfig.json
├── pdf/
│   ├── _html/{aegispay_live_flow.html, grow_frontend.html, sell_frontend.html}
│   └── build_{pdf,langgraph,v2,v3,v4,db,db_easy,db_simple}.py
├── scripts/
│   ├── ci/run-integration.sh
│   └── dev/{bootstrap.sh, bootstrap.ps1}
├── tests/
│   └── e2e/{playwright.config.ts, specs/checkout-flow.spec.ts}
├── workers/
│   ├── jobs/{__init__.py, hold_expiry.py, reconciliation.py}
│   ├── __init__.py · config.py · Dockerfile · main.py · pyproject.toml
│   ├── reconciliation.py · webhook_processor.py
├── .gitignore · CONTRIBUTING.md · Makefile · README.md · STRUCTURE.md
```
