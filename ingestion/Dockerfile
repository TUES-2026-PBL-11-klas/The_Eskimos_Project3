# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────────────────────
# uv-base: the package manager + the lockfiles. Cached unless deps change.
# Nothing from this stage reaches the production image — uv is build-time only.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS uv-base
WORKDIR /app
# Use the base image's interpreter; never let uv download a managed Python (it wouldn't
# exist in the runtime stage). Put the venv at a fixed path we copy out later.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
RUN pip install --no-cache-dir uv
# Lockfiles only → this layer caches unless deps change.
COPY pyproject.toml uv.lock ./

# prod deps only → /app/.venv. No dev group; the project itself isn't installed —
# the package is made importable at runtime via PYTHONPATH instead, so src/ isn't needed here.
FROM uv-base AS prod-deps
RUN uv sync --frozen --no-dev --no-install-project --python python3.11

# all deps incl. the dev group (pytest/ruff/mypy/pre-commit) → /app/.venv, for the test image.
FROM uv-base AS dev-deps
RUN uv sync --frozen --no-install-project --python python3.11

# ─────────────────────────────────────────────────────────────────────────────
# test: dev venv + full source + tests + tooling config. Fat by design; never shipped.
# Run with `docker compose run --rm test`. Compose bind-mounts src/ and tests/ so code
# edits and `ruff format` reflect on the host without a rebuild.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS test
WORKDIR /app
COPY --from=dev-deps /app/.venv /app/.venv
COPY pyproject.toml uv.lock alembic.ini ./
COPY src ./src
COPY migrations ./migrations
COPY tests ./tests
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1
CMD ["pytest", "--cov=ingestion", "--cov-report=term-missing"]

# ─────────────────────────────────────────────────────────────────────────────
# runtime: the production image (DEFAULT target). Slim base + prod venv + source +
# migrations only — no uv, no build toolchain, no dev deps, no tests.
# The compose ingestion job overrides CMD to also run migrations first; the cleanup
# job overrides it to run the retention worker.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=prod-deps /app/.venv /app/.venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1
CMD ["python", "-m", "ingestion.main"]
