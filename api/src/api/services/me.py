"""Current-user profile service.

Reads the account plus its preferences and applies partial updates. The users
session dependency commits on success, so this service only mutates ORM
instances (and creates a preferences row if one is somehow missing).
"""

from __future__ import annotations

from api.db.models.users import User, UserPreferences
from api.repository.users import UserRepository
from api.schemas.me import MeSchema, PreferencesSchema


class MeService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def _get_or_create_preferences(self, user_id: int) -> UserPreferences:
        prefs = await self._user_repo.get_preferences(user_id)
        if prefs is None:
            # Normally created at register-time; set explicit values so the schema
            # reads valid defaults even before the row is flushed.
            prefs = UserPreferences(user_id=user_id, default_lead_hours=24, timezone="Europe/Sofia")
            await self._user_repo.add_preferences(prefs)
        return prefs

    async def get_me(self, user: User) -> MeSchema:
        prefs = await self._get_or_create_preferences(user.id)
        return MeSchema(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            preferences=PreferencesSchema.model_validate(prefs),
        )

    async def update_me(
        self,
        user: User,
        display_name: str | None,
        default_lead_hours: int | None,
        timezone: str | None,
    ) -> MeSchema:
        if display_name is not None:
            user.display_name = display_name
        prefs = await self._get_or_create_preferences(user.id)
        if default_lead_hours is not None:
            prefs.default_lead_hours = default_lead_hours
        if timezone is not None:
            prefs.timezone = timezone
        return MeSchema(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            preferences=PreferencesSchema.model_validate(prefs),
        )
