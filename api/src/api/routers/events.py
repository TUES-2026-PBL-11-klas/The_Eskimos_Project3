"""Public events API.

Route registration order matters: ``/events/upcoming`` is declared before
``/events/{event_id}`` so FastAPI matches the literal segment first and never
treats the string "upcoming" as an integer ID.

All endpoints that return event data set ``Cache-Control: max-age=N, public``
where N comes from ``settings.cache_max_age_seconds`` (default 300 s).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from api.config import settings
from api.deps import EventServiceDep
from api.domain.exceptions import EventNotFoundError
from api.repository.events import EventFilters
from api.schemas.events import (
    CategoryWithCount,
    EventPage,
    EventSchema,
    EventStatsSchema,
    VenueSchema,
)

router = APIRouter(tags=["events"])

_CACHE_HEADER = f"max-age={settings.cache_max_age_seconds}, public"


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = _CACHE_HEADER


# ── /events/upcoming must come BEFORE /events/{event_id} ─────────────────────

@router.get("/events/upcoming")
async def upcoming_events(
    response: Response,
    service: EventServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    group_by: bool = False,
) -> list[EventSchema]:
    _cache(response)
    return await service.upcoming(limit=limit, group_by_category=group_by)


@router.get("/events/{event_id}")
async def get_event(
    event_id: int,
    response: Response,
    service: EventServiceDep,
) -> EventSchema:
    _cache(response)
    try:
        return await service.get_event(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/events")
async def list_events(
    response: Response,
    service: EventServiceDep,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    category: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    venue_id: Annotated[int | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EventPage:
    _cache(response)
    filters = EventFilters(
        date_from=date_from,
        date_to=date_to,
        category_slug=category,
        city=city,
        venue_id=venue_id,
        q=q,
        page=page,
        size=size,
    )
    return await service.list_events(filters)


# ── Non-event collection endpoints ───────────────────────────────────────────

@router.get("/categories")
async def list_categories(
    response: Response,
    service: EventServiceDep,
) -> list[CategoryWithCount]:
    _cache(response)
    return await service.categories()


@router.get("/venues")
async def list_venues(
    response: Response,
    service: EventServiceDep,
) -> list[VenueSchema]:
    _cache(response)
    return await service.venues()


@router.get("/search")
async def search_events(
    response: Response,
    service: EventServiceDep,
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[EventSchema]:
    _cache(response)
    return await service.search(q, limit=limit)


@router.get("/stats")
async def get_stats(
    response: Response,
    service: EventServiceDep,
) -> EventStatsSchema:
    _cache(response)
    return await service.stats()
