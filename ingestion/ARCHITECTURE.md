# EventHub — Ingestion Service

The **ingestion** service is one of three planned EventHub microservices (ingestion → API →
frontend). It is  **sole owner and writer** of the Postgres
`events` schema; the future API service reads from it through a SELECT-only role. Its job is one
thing: a **one-shot pass** that collects events from Bulgarian event sites, normalizes them
(bilingual BG/EN), de-duplicates, categorizes, and upserts them into Postgres — atomically — then
exits.

```
scrapers (parallel, Semaphore-gated) ──put──▶ asyncio.Queue (bounded) ──get──▶ pipeline ──▶ upsert
   asyncio.gather + Semaphore              backpressure                 run_one      single tx
```

Entry points (each a one-shot worker that exits when done):

| Worker | Module | What it does |
|--------|--------|--------------|
| Ingestion pass | `python -m ingestion.main` | scrape → pipeline → upsert, one transaction |
| Retention | `python -m ingestion.cleanup` | delete events older than `now − cleanup_grace_days` |
| Seed | `python -m ingestion.db.seed` | ~50 sample events for local dev (idempotent) |

---

## Scrapers

Sources follow the **Strategy + Factory** pattern (Open/Closed): every source is a
`BaseScraper` subclass implementing `async scrape() -> list[RawEvent]`, registered with the factory
via a decorator. Adding a source touches **no** pipeline or orchestrator code.

- [scrapers/base.py](src/ingestion/scrapers/base.py) — `BaseScraper` ABC. Shared HTTP lives in
  `_fetch_text` / `_fetch_json`: an `asyncio.Semaphore` gates outbound concurrency
  (`scrape_max_concurrency`, default 5) and **tenacity** retries transient HTTP failures (3
  attempts, exponential backoff) before raising `ScrapingError`.
- [scrapers/factory.py](src/ingestion/scrapers/factory.py) — `ScraperFactory` registry.
  `@ScraperFactory.register("name")` sets the stable `source_name` (also the DB source name);
  `create()` / `available()` instantiate and list them.
- [scrapers/__init__.py](src/ingestion/scrapers/__init__.py) — imports each module so registration
  runs as an import side effect (`main.py` does `import ingestion.scrapers` to trigger it).

### Registered sources (all verified live, 2026-05)

| `source_name` | Type | Target | How it parses | Notes |
|---------------|------|--------|---------------|-------|
| `ndk` | scraper | tickets.ndk.bg | `.eventEntryLong` blocks; event id from a `background-image` URL | All events at the National Palace of Culture, Sofia |
| `devbg` | scraper | dev.bg/events | "The Events Calendar" mobile-month blocks | Tech/business meetups → `education` category hint |
| `sofia_opera` | scraper | operasofia.bg | Monthly `/calendar/YYYY-MM`, current + next month | `category_hint="music"`; keywords refine (балет → theatre) |
| `visitsofia` | scraper | visitsofia.bg | Joomla JEvents list; de-dupes by `(id, date)` | Uses the robots-allowed `/component/` SEF route |
| `ticketmaster` | api | Discovery v2 API | JSON `_embedded.events` | Key from `settings`; **0 BG inventory today**, so returns `[]` — integration is correct & fixture-tested |

`enabled_sources` (CSV env var) selects which registered sources run a pass; empty = all.
Scrapers emit only loosely-typed `RawEvent`s with **raw** date strings — all parsing happens later
in the Normalizer.

### Live run observed during verification

```
sources: devbg, ndk, sofia_opera, ticketmaster, visitsofia
scraped: ndk 12, sofia_opera 39, visitsofia 123, devbg 13  (grand total 187)
deduplicated: 55 · invalid: 0 · duration ≈ 6s
```

---

## Pipeline

A **Chain of Responsibility** ([pipeline/base.py](src/ingestion/pipeline/base.py)): `Pipeline.run_one`
runs ordered `PipelineStep`s; each `process` returns the transformed event or `None` to drop it.
The chain transforms `RawEvent → NormalizedEvent`, so steps accept the union and narrow internally.
A misconfigured pipeline that never produces a `NormalizedEvent` fails loud rather than persisting a
raw event. Order is fixed in [main.py](src/ingestion/main.py):

1. **[Validator](src/ingestion/pipeline/validator.py)** — drops events missing required raw fields
   (`title`, `start_raw`, `url`); raises `InvalidEventDataError` (counted, batch continues).
2. **[Normalizer](src/ingestion/pipeline/normalizer.py)** — strips HTML (BeautifulSoup/lxml),
   collapses whitespace, parses the date to **UTC** (Bulgarian + English month names, `Europe/Sofia`
   source tz; no year in source ⇒ next upcoming occurrence), seeds the category from the source
   hint, and computes the deterministic `dedup_key` = `slug(title)|date|slug(city)`.
3. **[Deduplicator](src/ingestion/pipeline/deduplicator.py)** — two layers: an in-batch dict by
   `dedup_key` (drops the dupe and merges its missing `description`/`venue_name`/`venue_city` into
   the kept record, appending an `alternate_sources` entry), plus
   `EventRepository.find_duplicate` for events already persisted from a prior run.
4. **[Categorizer](src/ingestion/pipeline/categorizer.py)** — substring keyword match (bilingual)
   over title+description, ranked by hit count; falls back to the source hint, then
   `UNCATEGORIZED`.

### Domain model & taxonomy

[domain/models.py](src/ingestion/domain/models.py) keeps two deliberately separate Pydantic v2
shapes: **`RawEvent`** (loosely typed, mostly optional — what a scraper pulled) vs
**`NormalizedEvent`** (cleaned, typed, ready to persist).
[domain/categories.py](src/ingestion/domain/categories.py) defines the taxonomy — 7 real
categories (`music`, `sport`, `literature`, `education`, `cinema`, `theatre`, `art`) plus an
explicit `UNCATEGORIZED` fallback — and a bilingual `KEYWORD_MAP`. Short/ambiguous English tokens
are deliberately avoided (`run`, `art`, `dj`) to limit substring false positives.

### Orchestration & invariants ([main.py](src/ingestion/main.py))

- **Producer/consumer** — scrapers run in parallel via `asyncio.gather`, putting `RawEvent`s onto a
  bounded `asyncio.Queue` (maxsize 1000 → backpressure); a single consumer drains it through the
  pipeline; a sentinel marks end-of-stream.
- **Whole batch = one transaction** — the pass runs inside `session_scope()`; everything commits
  atomically or rolls back on any error.
- **One failing source never aborts the run** — a scraper raising `ScrapingError` is logged and
  skipped; an event failing validation/parsing is counted invalid and dropped.
- **Observability** — structured JSON logs via **structlog**; [metrics.py](src/ingestion/metrics.py)
  emits one `ingestion_run_complete` summary line (per-source counts, normalized, deduplicated,
  invalid, duration).

---

## Database

PostgreSQL 16, accessed with **SQLAlchemy 2.0 async** (`asyncpg`). All timestamps are
`TIMESTAMPTZ` (UTC).

- [db/orm.py](src/ingestion/db/orm.py) — typed ORM. Tables: **sources**, **venues**,
  **categories**, **events**. `events` has a unique `(source_id, external_id)`, indexes on
  `start_at`, `(category_id, start_at)`, `dedup_key`, and a **pg_trgm GIN** index on `title` for
  fuzzy search.
- [db/base.py](src/ingestion/db/base.py) — async engine, session factory, and `session_scope()`
  (`session.begin()` → commit on clean exit, rollback on error). This is the single-transaction
  boundary the orchestrator relies on.
- [repository/base.py](src/ingestion/repository/base.py) — generic `Repository[T]` interface
  (Dependency Inversion: higher layers depend on the abstraction, not SQLAlchemy).
- [repository/event_repository.py](src/ingestion/repository/event_repository.py) — the concrete
  repo:
  - **`upsert`** is a Postgres `ON CONFLICT (source_id, external_id) DO UPDATE` — idempotent within
    a source.
  - Source/venue/category use **cached get-or-create** to avoid round-trips when events share them.
  - Async forbids lazy IO, so read paths (`get`, `find_duplicate`) explicitly `selectinload`
    source/venue/category; write paths never touch relationships.
  - `delete_past(cutoff)` powers the retention worker; `touch_sources_last_run` stamps
    `last_run_at`.

### Migrations ([migrations/](migrations/))

Alembic, run through an **async** env ([migrations/env.py](migrations/env.py)) that pulls the URL
and metadata from the package (single source of truth).

- **0001 — initial schema**: all tables + indexes/constraints, creates the `pg_trgm` extension and
  the trigram GIN index, and creates the **SELECT-only `events_reader` role** for the downstream
  read-only API (the DB enforces the read boundary; no password in git).
- **0002 — trim schema**: drops columns/tables that were 100% NULL or unused in practice
  (`events.end_at`, price/currency columns, `venues.address/lat/lon`, and the `tags`/`event_tags`
  tagging tables).

[db/seed.py](src/ingestion/db/seed.py) inserts ~50 sample events across categories for local dev;
re-running is a no-op once the table has rows.

---

## Docker

Everything runs in Docker — **no local venv or Postgres needed**. `uv` manages dependencies
([pyproject.toml](pyproject.toml) + `uv.lock`); `.python-version` pins Python 3.11.

### Image ([Dockerfile](Dockerfile)) — multi-stage

- `uv-base` → `prod-deps` / `dev-deps` — build the venv (prod-only vs incl. the dev group); uv
  never reaches a final image.
- **`runtime`** (default, shipped) — slim base + prod venv + `src/` + `migrations/`. No uv, no
  toolchain, no tests. `CMD python -m ingestion.main`.
- **`test`** (fat, never shipped) — dev venv + source + tests + tooling. `CMD pytest --cov`.

### Compose ([docker-compose.yml](docker-compose.yml)) — services & profiles

| Service | Profile | Purpose |
|---------|---------|---------|
| `postgres` | (default) | The database; healthcheck-gated |
| `ingestion` | `jobs` | One pass: `alembic upgrade head && python -m ingestion.main` |
| `cleanup` | `jobs` | Retention worker: `python -m ingestion.cleanup` |
| `test` | `dev` | pytest + ruff + mypy; bind-mounts `src/`, `tests/`, `migrations/` for no-rebuild edits |

The `ingestion`/`cleanup` jobs override `DATABASE_URL` to reach Postgres over the compose network.
The `test` service mounts the Docker socket so **testcontainers** can spawn a throwaway Postgres,
reaching it via `host.docker.internal`.

### Task runner

[Makefile](Makefile) and [tasks.ps1](tasks.ps1) are 1:1 mirrors (use `tasks.ps1` on Windows). Run
from `ingestion/`:

```powershell
.\tasks.ps1 build              # build runtime + test images
.\tasks.ps1 up                 # start postgres
.\tasks.ps1 migrate            # alembic upgrade head
.\tasks.ps1 seed               # seed reference data
.\tasks.ps1 run                # one ingestion pass (migrate + scrape→pipeline→upsert)
.\tasks.ps1 clean-events       # retention worker
.\tasks.ps1 lint               # ruff check . && mypy src
.\tasks.ps1 fmt                # ruff format .
.\tasks.ps1 test               # full suite + coverage
.\tasks.ps1 test-unit          # unit only (no DB)
.\tasks.ps1 test-integration   # integration (testcontainers)
.\tasks.ps1 down               # stop everything, drop the volume
```

---

## Testing & quality gates

Markers: **`unit`** (fast, fully offline — scrapers parse saved HTML/JSON fixtures in
[tests/fixtures/](tests/fixtures/)) and **`integration`** (a throwaway `postgres:16` via
testcontainers — [tests/conftest.py](tests/conftest.py) starts it once, runs
`alembic upgrade head`, and truncates the schema per test). Code-quality gates run via Docker:
**ruff** (`E,F,I,UP,B,SIM`, line length 100) and **mypy --strict** (`.\tasks.ps1 lint`). No secret
literals live in code — all config comes through [config.py](src/ingestion/config.py).
(Repo-wide pre-commit / CI hooks live on a separate, dedicated branch.)

### Verification results (this environment)

| Check | Result |
|-------|--------|
| `docker compose build` (runtime + test) | ✅ built |
| `ruff check .` | ✅ All checks passed |
| `mypy src` (strict) | ✅ no issues in 31 source files |
| Unit tests | ✅ 13 passed |
| Integration tests | ✅ 6 passed |
| Full suite + coverage | ✅ **19 passed, 87% coverage** |
| Live migrate → ingestion pass | ✅ 187 scraped, 55 deduped, 0 invalid, persisted across all 8 categories |
| Retention worker | ✅ pruned past events by `start_at` cutoff |
