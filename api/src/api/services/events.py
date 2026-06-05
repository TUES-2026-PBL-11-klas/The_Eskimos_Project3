"""Application-layer logic for the public events surface.

This service sits between the router (HTTP concerns) and the repository
(persistence concerns). Its job is to translate domain objects to/from Pydantic
DTOs and to enforce business rules (e.g. raising EventNotFoundError on a missing
event so the router can map that to HTTP 404).
"""

from __future__ import annotations

import math

from api.domain.exceptions import EventNotFoundError
from api.repository.events import EventFilters, EventRepository
from api.schemas.events import (
    CategorySchema,
    CategoryWithCount,
    EventPage,
    EventSchema,
    EventStatsSchema,
    VenueSchema,
)


class EventService:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def get_event(self, event_id: int) -> EventSchema:
        event = await self._repo.get(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        return EventSchema.model_validate(event)

    async def list_events(self, filters: EventFilters) -> EventPage:
        events, total = await self._repo.list_events(filters)
        pages = math.ceil(total / filters.size) if filters.size else 0
        return EventPage(
            items=[EventSchema.model_validate(e) for e in events],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=pages,
        )

    async def upcoming(
        self, *, limit: int = 20, group_by_category: bool = False
    ) -> list[EventSchema]:
        events = await self._repo.upcoming(limit=limit, group_by_category=group_by_category)
        return [EventSchema.model_validate(e) for e in events]

    async def categories(self) -> list[CategoryWithCount]:
        rows = await self._repo.categories_with_counts()
        return [
            CategoryWithCount(
                category=CategorySchema.model_validate(cat),
                count=count,
            )
            for cat, count in rows
        ]

    async def venues(self) -> list[VenueSchema]:
        venues = await self._repo.venues()
        return [VenueSchema.model_validate(v) for v in venues]

    async def search(self, q: str, *, limit: int = 20) -> list[EventSchema]:
        events = await self._repo.search(q, limit=limit)
        return [EventSchema.model_validate(e) for e in events]

    async def stats(self) -> EventStatsSchema:
        s = await self._repo.stats()
        return EventStatsSchema(
            total_events=s.total_events,
            total_venues=s.total_venues,
            total_categories=s.total_categories,
            total_sources=s.total_sources,
        )
