.PHONY: up down psql migrate test lint run

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose run --rm db_migrate

psql:
	docker compose exec db psql -U aegispay_app -d aegispay

run:
	uvicorn app.main:app --reload

lint:
	ruff check .
	mypy app ai_runtime

test:
	pytest -q
