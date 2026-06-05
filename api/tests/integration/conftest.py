"""Integration test fixtures.

Spins up a throwaway ``postgres:16`` via testcontainers, loads ``seed/events_fixture.sql``
once per session, and provides each test with its own ``AsyncSession``. No alembic migrations
are run here — the fixture SQL creates the schema directly, mirroring what ingestion migrations
produce (the events DB is owned by ingestion, not by this service).

When tests run inside the ``test`` compose container, testcontainers spawns its own Postgres
and reaches it via ``host.docker.internal`` (set by ``TESTCONTAINERS_HOST_OVERRIDE`` in
docker-compose.yml). Unit tests do not import this conftest.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import asyncpg  # type: ignore[import-untyped]
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

_FIXTURE_SQL = Path(__file__).resolve().parent.parent.parent / "seed" / "events_fixture.sql"


async def _load_fixture(asyncpg_url: str) -> None:
    sql = _FIXTURE_SQL.read_text()
    conn = await asyncpg.connect(asyncpg_url)
    try:
        await conn.execute(sql)
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16", driver="asyncpg") as container:
        yield container


@pytest.fixture(scope="session")
def seeded_events_db_url(postgres_container: PostgresContainer) -> str:
    url = postgres_container.get_connection_url()
    asyncio.run(_load_fixture(url.replace("postgresql+asyncpg://", "postgresql://")))
    return url


@pytest_asyncio.fixture
async def db_session(seeded_events_db_url: str) -> AsyncIterator[AsyncSession]:
    # Per-test engine so connections are created and disposed within the same
    # function-scoped event loop that pytest-asyncio provides for each test.
    engine = create_async_engine(seeded_events_db_url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(seeded_events_db_url: str) -> AsyncIterator[AsyncClient]:
    """HTTP test client wired to the seeded throwaway DB via DI override.

    Overrides ``_get_events_session`` so every request in this test gets a real
    session against the testcontainers DB instead of the production events DB URL.
    A per-test engine is created and disposed here for the same event-loop
    isolation reason as ``db_session``.
    """
    from api.deps import _get_events_session
    from api.main import create_app

    engine = create_async_engine(seeded_events_db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[_get_events_session] = _override_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    await engine.dispose()
