"""SQLAlchemy implementation of the event repository.

Lazy/eager policy: relationships default to SQLAlchemy's lazy loading (fine for writes,
which never touch them). The read paths that reconstruct a ``NormalizedEvent``
(`get`, `find_duplicate`) would otherwise trigger lazy IO — illegal under async — so they
explicitly eager-load source/venue/category with ``selectinload``.

Get-or-create for sources/venues/categories is backed by per-run dict caches to avoid
repeated round-trips when many events share the same venue or category.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ingestion.db.orm import Category as CategoryORM
from ingestion.db.orm import Event, Source, Venue
from ingestion.domain.categories import Category
from ingestion.domain.models import NormalizedEvent
from ingestion.repository.base import Repository

# Columns refreshed when an upsert hits an existing (source_id, external_id) row.
_UPSERT_COLUMNS = (
    "title",
    "description",
    "start_at",
    "venue_id",
    "category_id",
    "url",
    "dedup_key",
    "raw_payload",
)


class EventRepository(Repository[NormalizedEvent]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._source_cache: dict[str, int] = {}
        self._category_cache: dict[str, int] = {}
        self._venue_cache: dict[tuple[str, str | None], int] = {}

    # --- get-or-create helpers (cached) -------------------------------------------------

    async def _get_or_create_source(self, name: str) -> int:
        if name in self._source_cache:
            return self._source_cache[name]
        source_id = await self._session.scalar(select(Source.id).where(Source.name == name))
        if source_id is None:
            # NormalizedEvent carries no source type; default to "scraper". Pre-seeded
            # sources (and Phase 5's setup) set the accurate type.
            source = Source(name=name, type="scraper")
            self._session.add(source)
            await self._session.flush()
            source_id = source.id
        self._source_cache[name] = source_id
        return source_id

    async def _get_or_create_category(self, category: Category) -> int:
        slug = category.value
        if slug in self._category_cache:
            return self._category_cache[slug]
        category_id = await self._session.scalar(
            select(CategoryORM.id).where(CategoryORM.slug == slug)
        )
        if category_id is None:
            row = CategoryORM(name=category.value.title(), slug=slug)
            self._session.add(row)
            await self._session.flush()
            category_id = row.id
        self._category_cache[slug] = category_id
        return category_id

    async def _get_or_create_venue(self, name: str | None, city: str | None) -> int | None:
        if not name:
            return None
        key = (name, city)
        if key in self._venue_cache:
            return self._venue_cache[key]
        stmt = select(Venue.id).where(Venue.name == name)
        stmt = stmt.where(Venue.city.is_(None) if city is None else Venue.city == city)
        venue_id = await self._session.scalar(stmt)
        if venue_id is None:
            venue = Venue(name=name, city=city)
            self._session.add(venue)
            await self._session.flush()
            venue_id = venue.id
        self._venue_cache[key] = venue_id
        return venue_id

    async def _resolve_fks(self, entity: NormalizedEvent) -> tuple[int, int, int | None]:
        source_id = await self._get_or_create_source(entity.source)
        category_id = await self._get_or_create_category(entity.category)
        venue_id = await self._get_or_create_venue(entity.venue_name, entity.venue_city)
        return source_id, category_id, venue_id

    def _values(
        self, entity: NormalizedEvent, source_id: int, category_id: int, venue_id: int | None
    ) -> dict[str, object]:
        return {
            "source_id": source_id,
            "external_id": entity.external_id,
            "title": entity.title,
            "description": entity.description,
            "start_at": entity.start_at,
            "venue_id": venue_id,
            "category_id": category_id,
            "url": entity.url,
            "dedup_key": entity.dedup_key,
            "raw_payload": entity.raw_payload,
        }

    # --- Repository interface ------------------------------------------------------------

    async def add(self, entity: NormalizedEvent) -> NormalizedEvent:
        source_id, category_id, venue_id = await self._resolve_fks(entity)
        event = Event(**self._values(entity, source_id, category_id, venue_id))
        self._session.add(event)
        await self._session.flush()
        return entity

    async def upsert(self, entity: NormalizedEvent) -> NormalizedEvent:
        """Insert, or refresh an existing row keyed by (source_id, external_id)."""
        source_id, category_id, venue_id = await self._resolve_fks(entity)
        stmt = pg_insert(Event).values(**self._values(entity, source_id, category_id, venue_id))
        set_: dict[str, Any] = {col: stmt.excluded[col] for col in _UPSERT_COLUMNS}
        set_["updated_at"] = func.now()
        stmt = stmt.on_conflict_do_update(index_elements=["source_id", "external_id"], set_=set_)
        await self._session.execute(stmt)
        return entity

    async def get(self, entity_id: int) -> NormalizedEvent | None:
        event = await self._session.scalar(
            select(Event)
            .where(Event.id == entity_id)
            .options(
                selectinload(Event.source),
                selectinload(Event.venue),
                selectinload(Event.category),
            )
        )
        return self._to_normalized(event) if event is not None else None

    async def find_duplicate(self, entity: NormalizedEvent) -> NormalizedEvent | None:
        """Indexed lookup by ``dedup_key`` (cross-source dedup identity)."""
        event = await self._session.scalar(
            select(Event)
            .where(Event.dedup_key == entity.dedup_key)
            .options(
                selectinload(Event.source),
                selectinload(Event.venue),
                selectinload(Event.category),
            )
            .limit(1)
        )
        return self._to_normalized(event) if event is not None else None

    async def touch_sources_last_run(self, names: list[str]) -> None:
        """Stamp `last_run_at = now()` on existing source rows named in `names`."""
        if not names:
            return
        await self._session.execute(
            update(Source).where(Source.name.in_(names)).values(last_run_at=func.now())
        )

    async def delete_past(self, cutoff: datetime) -> int:
        """Delete events whose `start_at` is before `cutoff`.

        The sources don't expose an event end time, so the start is the only signal for
        whether an event has passed. Returns the number of events deleted.
        """
        result = await self._session.execute(
            delete(Event).where(Event.start_at < cutoff)
        )
        return cast("CursorResult[Any]", result).rowcount

    # --- mapping -------------------------------------------------------------------------

    @staticmethod
    def _to_normalized(event: Event) -> NormalizedEvent:
        category = Category.UNCATEGORIZED
        if event.category is not None:
            try:
                category = Category(event.category.slug)
            except ValueError:
                category = Category.UNCATEGORIZED
        venue = event.venue
        return NormalizedEvent(
            source=event.source.name,
            external_id=event.external_id,
            title=event.title,
            description=event.description,
            start_at=event.start_at,
            url=event.url,
            venue_name=venue.name if venue else None,
            venue_city=venue.city if venue else None,
            category=category,
            dedup_key=event.dedup_key,
            raw_payload=event.raw_payload,
        )
