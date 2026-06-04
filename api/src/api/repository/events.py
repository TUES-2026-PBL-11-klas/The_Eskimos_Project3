"""Read-only EventRepository.

No write methods exist on this class — the ingestion service is the sole owner and
writer of the events schema. ``selectinload`` is used on every read path that returns
relationships because asyncpg forbids lazy IO outside the session context.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.db.models.events import Category, Event, Venue
from api.repository.base import AsyncRepository


@dataclass
class EventFilters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    category_slug: str | None = None
    city: str | None = None
    q: str | None = None
    page: int = 1
    size: int = 20


@dataclass
class EventStats:
    total_events: int
    total_venues: int
    total_categories: int
    total_sources: int


_RELATIONSHIPS = (
    selectinload(Event.source),
    selectinload(Event.venue),
    selectinload(Event.category),
)


class EventRepository(AsyncRepository[Event]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── single-event ────────────────────────────────────────────────────────

    async def get(self, entity_id: int) -> Event | None:
        result = await self._session.execute(
            select(Event).options(*_RELATIONSHIPS).where(Event.id == entity_id)
        )
        return result.scalar_one_or_none()

    # ── collection queries ───────────────────────────────────────────────────

    async def list_events(self, filters: EventFilters) -> tuple[list[Event], int]:
        count_result = await self._session.execute(
            self._apply_filters(select(func.count(Event.id)), filters)
        )
        total: int = count_result.scalar_one()

        stmt = (
            self._apply_filters(select(Event).options(*_RELATIONSHIPS), filters)
            .order_by(Event.start_at)
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars()), total

    async def upcoming(self, *, limit: int = 20, group_by_category: bool = False) -> list[Event]:
        future = Event.start_at >= func.now()

        if not group_by_category:
            result = await self._session.execute(
                select(Event)
                .options(*_RELATIONSHIPS)
                .where(future)
                .order_by(Event.start_at)
                .limit(limit)
            )
            return list(result.scalars())

        # One upcoming event per category via ROW_NUMBER() OVER (PARTITION BY category_id)
        rn = func.row_number().over(
            partition_by=Event.category_id,
            order_by=Event.start_at,
        ).label("rn")
        subq = select(Event.id, rn).where(future).subquery()
        result = await self._session.execute(
            select(Event)
            .options(*_RELATIONSHIPS)
            .join(subq, Event.id == subq.c.id)
            .where(subq.c.rn == 1)
            .order_by(Event.start_at)
        )
        return list(result.scalars())

    async def categories_with_counts(self) -> list[tuple[Category, int]]:
        rows = (
            await self._session.execute(
                select(Category, func.count(Event.id))
                .join(Event, Event.category_id == Category.id)
                .group_by(Category.id)
                .order_by(Category.name)
            )
        ).all()
        return [(row[0], row[1]) for row in rows]

    async def venues(self) -> list[Venue]:
        result = await self._session.execute(select(Venue).order_by(Venue.name))
        return list(result.scalars())

    async def search(self, q: str, *, limit: int = 20) -> list[Event]:
        result = await self._session.execute(
            select(Event)
            .options(*_RELATIONSHIPS)
            .where(Event.title.ilike(f"%{q}%"))
            .order_by(Event.start_at)
            .limit(limit)
        )
        return list(result.scalars())

    async def stats(self) -> EventStats:
        row = (
            await self._session.execute(
                select(
                    func.count(Event.id),
                    func.count(distinct(Event.venue_id)),
                    func.count(distinct(Event.category_id)),
                    func.count(distinct(Event.source_id)),
                )
            )
        ).one()
        return EventStats(
            total_events=row[0],
            total_venues=row[1],
            total_categories=row[2],
            total_sources=row[3],
        )

    # ── internal ─────────────────────────────────────────────────────────────

    def _apply_filters(self, stmt: Select[Any], f: EventFilters) -> Select[Any]:
        """Apply optional WHERE/JOIN clauses; only active when the filter value is set."""
        if f.date_from is not None:
            stmt = stmt.where(Event.start_at >= f.date_from)
        if f.date_to is not None:
            stmt = stmt.where(Event.start_at <= f.date_to)
        if f.category_slug is not None:
            stmt = stmt.join(Event.category).where(Category.slug == f.category_slug)
        if f.city is not None:
            stmt = stmt.join(Event.venue).where(Venue.city == f.city)
        if f.q is not None:
            stmt = stmt.where(Event.title.ilike(f"%{f.q}%"))
        return stmt
