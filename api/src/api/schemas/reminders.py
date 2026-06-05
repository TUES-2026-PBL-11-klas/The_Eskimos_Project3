from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReminderRequest(BaseModel):
    lead_hours: int | None = None
    remind_at: datetime | None = None


class ReminderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    saved_event_id: int
    remind_at: datetime
    status: str
    created_at: datetime
