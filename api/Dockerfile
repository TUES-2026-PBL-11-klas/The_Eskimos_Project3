# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────────────────────
# uv-base: the package manager + the lockfiles. Cached unless deps change.
# Nothing from this stage reaches the production image — uv is build-time only.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS uv-base
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./

# prod deps only → /app/.venv. No dev group; the project itself isn't installed —
# the package is made importable at runtime via PYTHONPATH instead.
FROM uv-base AS prod-deps
RUN uv sync --frozen --no-dev --no-install-project --python python3.11

# all deps incl. the dev group (pytest/ruff/mypy) → /app/.venv, for the test image.
FROM uv-base AS dev-deps
RUN uv sync --frozen --no-install-project --python python3.11

# ─────────────────────────────────────────────────────────────────────────────
# test: dev venv + full source + tests + tooling config. Fat by design; never shipped.
# Compose bind-mounts src/ and tests/ so edits and `ruff format` reflect without a rebuild.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS test
WORKDIR /app
COPY --from=dev-deps /app/.venv /app/.venv
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY tests ./tests
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1
CMD ["pytest", "--cov=api", "--cov-report=term-missing"]

# ─────────────────────────────────────────────────────────────────────────────
# runtime: the production image (DEFAULT target). Slim base + prod venv + source only —
# no uv, no build toolchain, no dev deps, no tests. Serves the API with uvicorn.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
WORKDIR /app
# Run as a non-root user; nothing is written to the image at runtime.
RUN groupadd --system app && useradd --system --gid app --no-create-home app
COPY --from=prod-deps /app/.venv /app/.venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini .
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
