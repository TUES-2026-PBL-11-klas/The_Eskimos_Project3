"""Test fixtures.

Integration tests run against a throwaway PostgreSQL 16 container managed by
``testcontainers`` (the plan's Phase 6 approach — no pre-existing database required).
The session fixture starts the container, points the app's config at it, and runs
``alembic upgrade head`` once; each test gets a freshly-truncated schema. Unit tests need
none of this and stay fully offline.

When the suite itself runs inside the ``test`` compose container, testcontainers talks to
the host Docker daemon through the mounted socket and reaches the Postgres it spawns via
``host.docker.internal`` (see ``TESTCONTAINERS_HOST_OVERRIDE`` in docker-compose.yml).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

import ingestion.db.base as db_base
from ingestion import config as config_module
from ingestion.domain.models import RawEvent
from ingestion.scrapers.base import BaseScraper

_INGESTION_DIR = Path(__file__).resolve().parent.parent
_TABLES = ("events", "categories", "venues", "sources")


@pytest.fixture(scope="session")
def _postgres_container() -> Iterator[PostgresContainer]:
    # asyncpg driver so get_connection_url() yields a postgresql+asyncpg:// URL directly.
    with PostgresContainer("postgres:16", driver="asyncpg") as container:
        yield container


@pytest.fixture(scope="session")
def test_database_url(_postgres_container: PostgresContainer) -> str:
    return _postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def _migrated_database(test_database_url: str) -> str:
    # Point the app's config at the container before migrating / using it, then upgrade once.
    config_module.settings.database_url = test_database_url
    cfg = Config(str(_INGESTION_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_INGESTION_DIR / "migrations"))
    command.upgrade(cfg, "head")
    return test_database_url


@pytest_asyncio.fixture
async def db_session(_migrated_database: str) -> AsyncIterator[AsyncSession]:
    # Per-test engine, created/disposed within this test's event loop. Reassign the app's
    # globals so session_scope()/seed()/main.run() use the test database too.
    engine = create_async_engine(_migrated_database)
    db_base.engine = engine
    db_base.async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    try:
        async with db_base.async_session_factory() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.fixture
def fake_raw_events() -> list[RawEvent]:
    """Canned RawEvents for pipeline tests (no network). Includes a cross-source dup + invalid."""
    return [
        RawEvent(
            source="fake",
            external_id="f-1",
            title="Jazz Concert at the Hall",
            start_raw="2030-06-01 20:00",
            url="https://example.com/f-1",
            venue_name="Test Hall",
            venue_city="Sofia",
        ),
        RawEvent(
            source="fake",
            external_id="f-2",
            title="Modern Art Exhibition",
            start_raw="2030-06-02 18:00",
            url="https://example.com/f-2",
            venue_name="Test Gallery",
            venue_city="Sofia",
        ),
        RawEvent(
            source="other",
            external_id="o-1",
            title="Jazz Concert at the Hall",
            start_raw="2030-06-01 20:00",
            url="https://example.com/o-1",
            venue_city="Sofia",
        ),
        RawEvent(source="fake", external_id="bad", title="No Date", url="https://x"),
    ]


class FakeScraper(BaseScraper):
    """Network-free scraper used to drive main.run() in tests."""

    source_type = "scraper"
    canned: list[RawEvent] = []

    async def scrape(self) -> list[RawEvent]:
        return list(self.canned)


@pytest.fixture
def fake_scraper_cls() -> type[FakeScraper]:
    return FakeScraper
