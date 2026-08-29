.PHONY: up down psql migrate test lint type smoke run dev

up:
	docker compose up -d

down:
	docker compose down

dev:
	docker compose up --build

migrate:
	docker compose run --rm db_migrate

psql:
	docker compose exec db psql -U aegispay_app -d aegispay

run:
	uvicorn api.main:app --reload

lint:
	ruff check .
	ruff format --check .

# mypy `files` are relative to the repo root, so point it at the config there.
type:
	cd .. && mypy --config-file api/pyproject.toml

test:
	pytest -q

smoke:
	pytest -q tests/unit/test_smoke.py
