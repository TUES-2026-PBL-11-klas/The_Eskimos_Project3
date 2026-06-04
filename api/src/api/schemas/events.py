"""Pydantic response schemas for the public events API.

These are DTOs — intentionally a subset of the ORM models. Only columns present
after migration 0002 are exposed: no ``end_at``, no price columns, no tags.
``from_attributes=True`` on every schema lets Pydantic read directly from ORM
instances without an explicit conversion step.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str


class VenueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str | None


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    start_at: datetime
    url: str
    source: SourceSchema | None
    venue: VenueSchema | None
    category: CategorySchema | None
    created_at: datetime
    updated_at: datetime


class EventPage(BaseModel):
    """Paginated event list.  ``pages`` is always ceil(total / size)."""

    items: list[EventSchema]
    total: int
    page: int
    size: int
    pages: int


class CategoryWithCount(BaseModel):
    category: CategorySchema
    count: int


class EventStatsSchema(BaseModel):
    total_events: int
    total_venues: int
    total_categories: int
    total_sources: int
