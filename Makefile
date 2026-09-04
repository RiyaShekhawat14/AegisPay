.PHONY: up down dev migrate test lint type smoke run verify health

# Local dev (delegates to api/). See deploy/compose/.
up:
	docker compose -f deploy/compose/docker-compose.yml up -d
down:
	docker compose -f deploy/compose/docker-compose.yml down
dev:
	docker compose -f deploy/compose/docker-compose.yml up --build
migrate:
	docker compose -f deploy/compose/docker-compose.yml run --rm db_migrate

run:
	cd api && uvicorn api.main:app --reload

# Health check: every container must be running + its health/gate reachable.
health:
	@echo "== containers ==" && docker compose -f deploy/compose/docker-compose.yml ps --format "table {{.Service}}\t{{.Status}}"
	@echo "== control plane ==" && curl -sf http://localhost:8000/v1/health >/dev/null && echo "health: ok" || echo "health: FAIL"
	@echo "== ai runtime ==" && curl -sf http://localhost:8001/openapi.json >/dev/null && echo "openapi: ok" || echo "openapi: FAIL"
	@echo "== frontend ==" && curl -sf http://localhost:3002/ >/dev/null && echo "web: ok" || echo "web: FAIL"

# mypy's `files` globs are relative to the repo root, so run from here, not api/.
lint:
	cd api && ruff check .
type:
	mypy --config-file api/pyproject.toml
test:
	cd api && pytest -q tests/unit
smoke:
	cd api && pytest -q tests/unit/test_smoke.py
verify: lint type test
