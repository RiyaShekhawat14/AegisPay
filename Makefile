.PHONY: up down dev migrate test lint type smoke run verify

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
