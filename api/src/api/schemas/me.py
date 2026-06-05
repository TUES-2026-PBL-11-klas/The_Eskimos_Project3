"""Schemas for the current-user profile and preferences endpoints.

``GET /me`` returns the account plus its preferences; ``PATCH /me`` accepts a
partial update where every field is optional (only provided fields are written).
Preferences are limited to what the ``user_preferences`` table actually stores:
``default_lead_hours`` and ``timezone`` (no category/city arrays).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PreferencesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    default_lead_hours: int
    timezone: str


class MeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    created_at: datetime
    preferences: PreferencesSchema


class MeUpdateRequest(BaseModel):
    """Partial profile/preferences update. All fields optional."""

    display_name: str | None = None
    default_lead_hours: int | None = None
    timezone: str | None = None
