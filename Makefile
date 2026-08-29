.PHONY: up down migrate test lint type run

# Local dev (delegates to api/). See deploy/compose/.
up:
	docker compose -f deploy/compose/docker-compose.yml up -d
down:
	docker compose -f deploy/compose/docker-compose.yml down
migrate:
	docker compose -f deploy/compose/docker-compose.yml run --rm db_migrate

run:
	cd api && uvicorn api.main:app --reload

lint:
	cd api && ruff check .
type:
	cd api && mypy --config-file pyproject.toml
test:
	cd api && pytest -q tests/unit
