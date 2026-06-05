"""Reminder service.

Business rules:
  - remind_at is derived from lead_hours, explicit remind_at, or the user's default_lead_hours
    (checked in that priority order: explicit remind_at > lead_hours > preference default).
  - A reminder whose computed remind_at is already in the past is rejected (ValueError → HTTP 422).
  - cancel sets status to "cancelled" rather than deleting the row so list history is preserved.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.db.models.users import Reminder
from api.domain.exceptions import EventNotFoundError, ReminderNotFoundError
from api.repository.reminders import ReminderRepository
from api.repository.saved import SavedEventRepository
from api.repository.users import UserRepository
from api.schemas.reminders import ReminderSchema


class ReminderService:
    def __init__(
        self,
        saved_repo: SavedEventRepository,
        reminder_repo: ReminderRepository,
        user_repo: UserRepository,
    ) -> None:
        self._saved_repo = saved_repo
        self._reminder_repo = reminder_repo
        self._user_repo = user_repo

    async def create(
        self,
        user_id: int,
        saved_id: int,
        lead_hours: int | None,
        remind_at_override: datetime | None,
    ) -> ReminderSchema:
        saved = await self._saved_repo.get_for_user(saved_id, user_id)
        if saved is None:
            raise EventNotFoundError(saved_id)

        if remind_at_override is not None:
            # Normalise naive datetimes to UTC (client should always send TZ-aware).
            if remind_at_override.tzinfo is None:
                final_remind_at = remind_at_override.replace(tzinfo=UTC)
            else:
                final_remind_at = remind_at_override
        elif lead_hours is not None:
            final_remind_at = saved.start_at - timedelta(hours=lead_hours)
        else:
            prefs = await self._user_repo.get_preferences(user_id)
            hours = prefs.default_lead_hours if prefs is not None else 24
            final_remind_at = saved.start_at - timedelta(hours=hours)

        if final_remind_at <= datetime.now(UTC):
            raise ValueError("remind_at is in the past")

        reminder = Reminder(
            saved_event_id=saved.id,
            user_id=user_id,
            remind_at=final_remind_at,
            status="pending",
        )
        return ReminderSchema.model_validate(await self._reminder_repo.add(reminder))

    async def list_for_user(self, user_id: int) -> list[ReminderSchema]:
        reminders = await self._reminder_repo.list_by_user(user_id)
        return [ReminderSchema.model_validate(r) for r in reminders]

    async def cancel(self, user_id: int, reminder_id: int) -> None:
        reminder = await self._reminder_repo.get_for_user(reminder_id, user_id)
        if reminder is None:
            raise ReminderNotFoundError(reminder_id)
        await self._reminder_repo.cancel(reminder)

    async def list_due(self, user_id: int) -> list[ReminderSchema]:
        reminders = await self._reminder_repo.list_due_for_user(user_id, datetime.now(UTC))
        return [ReminderSchema.model_validate(r) for r in reminders]
