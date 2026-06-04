.PHONY: build up down migrate seed run lint fmt test test-unit test-integration

# Everything runs in Docker — no local venv or Postgres required. `tasks.ps1` mirrors this 1:1.
# The events DB is the ingestion service's Postgres: start it first from `ingestion/` with
# `make up` (it exposes port 5432 on the host).

build:            ## build the runtime + test images
	docker compose --profile dev build

up:               ## start the API in the background
	docker compose up -d api

down:             ## stop everything and drop volumes
	docker compose down -v

migrate:          ## apply alembic migrations against the users db (Phase 4+)
	docker compose run --rm api alembic upgrade head

seed:             ## load the local events fixture (Phase 1+; integration tests use it directly)
	docker compose run --rm test python -m api.db.seed_events

run:              ## run the API in the foreground
	docker compose up api

lint:             ## ruff + mypy in the test image
	docker compose run --rm test sh -c "ruff check . && mypy src"

fmt:              ## auto-format (writes back to host via bind mount)
	docker compose run --rm test ruff format .

test:             ## full suite + coverage
	docker compose run --rm test

test-unit:        ## unit tests only (no database)
	docker compose run --rm test pytest -m unit

test-integration: ## integration tests (testcontainers)
	docker compose run --rm test pytest -m integration
