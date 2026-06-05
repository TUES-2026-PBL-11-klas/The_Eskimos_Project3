"""Integration tests for the users database — Phase 4.

Covers:
  - Migration roundtrip: upgrade → verify tables exist → downgrade → verify tables gone
  - Re-upgrade: ensures the migration is re-runnable from base
  - /health endpoint: both databases (events + users) report healthy
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg  # type: ignore[import-untyped]
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def users_postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16", driver="asyncpg") as container:
        yield container


@pytest.fixture(scope="session")
def users_db_url(users_postgres_container: PostgresContainer) -> str:
    """Return the asyncpg URL of a fresh users-DB container with migrations applied."""
    return users_postgres_container.get_connection_url()


def _run_alembic(command: str, url: str) -> None:
    """Run an alembic command against *url*.

    ``migrations/env.py`` reads ``settings.users_db_url`` and passes it to the engine, so we
    temporarily patch the singleton before alembic loads env.py. This avoids the module-caching
    problem where ``env.py`` overwrites the programmatically set URL with the settings default.
    """
    from alembic import command as alembic_cmd
    from alembic.config import Config

    import api.config as config_module

    original_url = config_module.settings.users_db_url
    config_module.settings.users_db_url = url  # type: ignore[misc]
    try:
        cfg = Config("alembic.ini")
        if command == "upgrade":
            alembic_cmd.upgrade(cfg, "head")
        elif command == "downgrade":
            alembic_cmd.downgrade(cfg, "base")
    finally:
        config_module.settings.users_db_url = original_url  # type: ignore[misc]


async def _table_names(url: str) -> set[str]:
    conn = await asyncpg.connect(url.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        return {row["tablename"] for row in rows}
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Migration roundtrip
# ---------------------------------------------------------------------------

EXPECTED_TABLES = {"users", "user_preferences", "sessions", "saved_events", "reminders"}


@pytest.mark.integration
def test_migration_upgrade_creates_all_tables(users_db_url: str) -> None:
    _run_alembic("upgrade", users_db_url)
    tables = asyncio.run(_table_names(users_db_url))
    assert EXPECTED_TABLES.issubset(tables)


@pytest.mark.integration
def test_migration_downgrade_drops_all_tables(users_db_url: str) -> None:
    # Depends on test_migration_upgrade_creates_all_tables running first (same session fixture).
    _run_alembic("downgrade", users_db_url)
    tables = asyncio.run(_table_names(users_db_url))
    assert EXPECTED_TABLES.isdisjoint(tables)


@pytest.mark.integration
def test_migration_re_upgrade_is_idempotent(users_db_url: str) -> None:
    _run_alembic("upgrade", users_db_url)
    tables = asyncio.run(_table_names(users_db_url))
    assert EXPECTED_TABLES.issubset(tables)


# ---------------------------------------------------------------------------
# /health endpoint — both DBs healthy
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def health_client(
    seeded_events_db_url: str,
    users_db_url: str,
) -> AsyncIterator[AsyncClient]:
    """HTTP test client with both DB session factories patched to testcontainers URLs."""
    import api.routers.system as system_module

    events_engine = create_async_engine(seeded_events_db_url)
    users_engine_tc = create_async_engine(users_db_url)
    events_factory = async_sessionmaker(events_engine, expire_on_commit=False)
    users_factory = async_sessionmaker(users_engine_tc, expire_on_commit=False)

    # Preserve originals so pytest teardown can restore them.
    original_events = system_module.events_session
    original_users = system_module.users_session

    @asynccontextmanager
    async def _events() -> AsyncIterator[AsyncSession]:
        async with events_factory() as s:
            yield s

    @asynccontextmanager
    async def _users() -> AsyncIterator[AsyncSession]:
        async with users_factory() as s:
            yield s

    system_module.events_session = _events  # type: ignore[assignment]
    system_module.users_session = _users  # type: ignore[assignment]

    from api.main import create_app

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    system_module.events_session = original_events
    system_module.users_session = original_users
    await events_engine.dispose()
    await users_engine_tc.dispose()


@pytest.mark.integration
async def test_health_both_dbs_healthy(health_client: AsyncClient) -> None:
    r = await health_client.get("/health")
    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert data["status"] == "ok"
    assert data["databases"]["events"] == "healthy"
    assert data["databases"]["users"] == "healthy"


@pytest.mark.integration
async def test_health_response_structure(health_client: AsyncClient) -> None:
    r = await health_client.get("/health")
    data: dict[str, Any] = r.json()
    assert "status" in data
    assert "databases" in data
    assert set(data["databases"].keys()) == {"events", "users"}
