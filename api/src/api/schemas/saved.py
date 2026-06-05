from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SavedEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    event_id: int | None
    title: str
    start_at: datetime
    venue_name: str | None
    city: str | None
    category: str | None
    url: str
    saved_at: datetime


class CalendarDaySchema(BaseModel):
    date: str
    events: list[SavedEventSchema]


class CalendarSchema(BaseModel):
    days: list[CalendarDaySchema]
