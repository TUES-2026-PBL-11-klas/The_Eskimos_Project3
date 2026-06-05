"""Integration tests against a real Postgres (the auto-managed <db>_test database)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import ingestion.db.base as db_base
import ingestion.main as main_module
from ingestion import config as config_module
from ingestion.db.orm import Event
from ingestion.db.seed import seed
from ingestion.domain.models import NormalizedEvent, RawEvent
from ingestion.exceptions import InvalidEventDataError
from ingestion.pipeline.base import Pipeline
from ingestion.pipeline.categorizer import Categorizer
from ingestion.pipeline.deduplicator import Deduplicator
from ingestion.pipeline.normalizer import Normalizer
from ingestion.pipeline.validator import Validator
from ingestion.repository.event_repository import EventRepository
from ingestion.scrapers.factory import ScraperFactory

pytestmark = pytest.mark.integration


def _ne(**overrides: Any) -> NormalizedEvent:
    base: dict[str, Any] = {
        "source": "itest",
        "external_id": "1",
        "title": "Title",
        "start_at": datetime(2030, 6, 1, 17, tzinfo=UTC),
        "url": "http://x",
        "dedup_key": "dk-1",
    }
    base.update(overrides)
    return NormalizedEvent(**base)


async def test_full_ingestion_pipeline_writes_to_db(
    db_session: AsyncSession, fake_raw_events: list[RawEvent]
) -> None:
    repo = EventRepository(db_session)
    pipeline = Pipeline([Validator(), Normalizer(), Deduplicator(repo), Categorizer()])

    persisted = []
    for raw in fake_raw_events:
        try:
            event = await pipeline.run_one(raw)
        except InvalidEventDataError:
            continue
        if event is not None:
            persisted.append(event)
    for event in persisted:
        await repo.upsert(event)
    await db_session.flush()

    # f-1 (music), f-2 (art), o-1 dup of f-1 (dropped), bad (invalid) → 2 rows.
    total = await db_session.scalar(select(func.count()).select_from(Event))
    assert total == 2
    slugs = (
        (
            await db_session.execute(
                text("SELECT c.slug FROM events e JOIN categories c ON c.id = e.category_id")
            )
        )
        .scalars()
        .all()
    )
    assert set(slugs) == {"music", "art"}


async def test_upsert_is_idempotent(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    event = _ne(source="up", external_id="u1", dedup_key="up-key", title="Up Event")
    await repo.upsert(event)
    await repo.upsert(event)
    await db_session.flush()
    total = await db_session.scalar(
        select(func.count()).select_from(Event).where(Event.external_id == "u1")
    )
    assert total == 1


async def test_find_duplicate_uses_dedup_key(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    await repo.upsert(_ne(source="fd", external_id="fd1", dedup_key="find-key"))
    await db_session.flush()

    match = await repo.find_duplicate(_ne(source="fd2", external_id="x", dedup_key="find-key"))
    assert match is not None
    miss = await repo.find_duplicate(_ne(dedup_key="no-such-key"))
    assert miss is None


async def test_events_reader_role_is_read_only(
    db_session: AsyncSession, test_database_url: str
) -> None:
    # Create a login role inheriting the SELECT-only events_reader (committed). Give it a
    # password so the connection works under real password auth (Docker Postgres), not just
    # trust-based local auth.
    async with db_base.engine.begin() as conn:
        await conn.execute(text("DROP ROLE IF EXISTS events_reader_login"))
        await conn.execute(text("CREATE ROLE events_reader_login LOGIN INHERIT PASSWORD 'reader'"))
        await conn.execute(text("GRANT events_reader TO events_reader_login"))

    reader_url = make_url(test_database_url).set(username="events_reader_login", password="reader")
    reader_engine = create_async_engine(reader_url.render_as_string(hide_password=False))
    try:
        async with reader_engine.connect() as conn:
            await conn.execute(text("SELECT count(*) FROM events"))  # allowed
            with pytest.raises(Exception) as exc_info:
                await conn.execute(
                    text(
                        "INSERT INTO events "
                        "(source_id, external_id, title, start_at, url, dedup_key, raw_payload) "
                        "VALUES (1, 'x', 'x', now(), 'x', 'x', '{}'::jsonb)"
                    )
                )
            assert "denied" in str(exc_info.value).lower()
    finally:
        await reader_engine.dispose()
        async with db_base.engine.begin() as conn:
            await conn.execute(text("DROP ROLE IF EXISTS events_reader_login"))


async def test_seed_populates_and_is_idempotent(db_session: AsyncSession) -> None:
    await seed()
    await seed()  # second run is a no-op
    total = await db_session.scalar(select(func.count()).select_from(Event))
    assert total == 50


async def test_main_run_persists_events(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    fake_scraper_cls: type,
) -> None:
    canned = [
        RawEvent(
            source="fake",
            external_id="m-1",
            title="Symphony concert",
            start_raw="2030-07-01 19:00",
            url="https://example.com/m-1",
            venue_city="Sofia",
        ),
        RawEvent(
            source="fake",
            external_id="m-2",
            title="Painting exhibition",
            start_raw="2030-07-02 10:00",
            url="https://example.com/m-2",
            venue_city="Sofia",
        ),
    ]
    monkeypatch.setattr(fake_scraper_cls, "canned", canned)
    monkeypatch.setitem(ScraperFactory._registry, "fake", fake_scraper_cls)
    monkeypatch.setattr(config_module.settings, "enabled_sources", ["fake"])

    await main_module.run()

    total = await db_session.scalar(select(func.count()).select_from(Event))
    assert total == 2
