.PHONY: build up down migrate seed run clean-events lint fmt test test-unit test-integration

# Everything runs in Docker — no local venv or Postgres required. `tasks.ps1` mirrors this 1:1.

build:            ## build the runtime + test images
	docker compose --profile jobs --profile dev build

up:               ## start postgres (the database) in the background
	docker compose up -d postgres

down:             ## stop everything and drop the postgres volume
	docker compose down -v

migrate:          ## apply alembic migrations against the compose db
	docker compose run --rm ingestion alembic upgrade head

seed:             ## seed reference data
	docker compose run --rm ingestion python -m ingestion.db.seed

run:              ## one ingestion pass (migrate + scrape→pipeline→upsert)
	docker compose run --rm ingestion

clean-events:     ## prune events that have already passed (retention worker)
	docker compose run --rm cleanup

lint:             ## ruff + mypy in the test image
	docker compose run --rm test sh -c "ruff check . && mypy src"

fmt:              ## auto-format (writes back to host via bind mount)
	docker compose run --rm test ruff format .

test:             ## full suite + coverage
	docker compose run --rm test

test-unit:        ## unit tests only (no database)
	docker compose run --rm test pytest -m unit

test-integration: ## integration tests (needs the compose db)
	docker compose run --rm test pytest -m integration
