"""Repository for the ``reminders`` table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.db.models.users import Reminder, SavedEvent
from api.repository.base import AsyncRepository


class ReminderRepository(AsyncRepository[Reminder]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: int) -> Reminder | None:
        result = await self._session.execute(
            select(Reminder)
            .options(selectinload(Reminder.saved_event))
            .where(Reminder.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_for_user(self, reminder_id: int, user_id: int) -> Reminder | None:
        """Fetch a reminder only if it belongs to the given user (ownership check)."""
        result = await self._session.execute(
            select(Reminder)
            .options(selectinload(Reminder.saved_event))
            .where(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Reminder]:
        result = await self._session.execute(
            select(Reminder)
            .options(selectinload(Reminder.saved_event))
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars())

    async def list_due(self, now: datetime) -> list[Reminder]:
        """Pending reminders whose remind_at has passed but whose event hasn't started yet."""
        result = await self._session.execute(
            select(Reminder)
            .join(SavedEvent, Reminder.saved_event_id == SavedEvent.id)
            .options(selectinload(Reminder.saved_event))
            .where(
                Reminder.status == "pending",
                Reminder.remind_at <= now,
                SavedEvent.start_at > now,
            )
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars())

    async def list_due_for_user(self, user_id: int, now: datetime) -> list[Reminder]:
        """Due reminders scoped to a single user (for the /me/reminders/due endpoint)."""
        result = await self._session.execute(
            select(Reminder)
            .join(SavedEvent, Reminder.saved_event_id == SavedEvent.id)
            .options(selectinload(Reminder.saved_event))
            .where(
                Reminder.user_id == user_id,
                Reminder.status == "pending",
                Reminder.remind_at <= now,
                SavedEvent.start_at > now,
            )
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars())

    async def add(self, reminder: Reminder) -> Reminder:
        """Persist a new reminder and flush so ``reminder.id`` is populated."""
        self._session.add(reminder)
        await self._session.flush()
        return reminder

    async def cancel(self, reminder: Reminder) -> None:
        """Set status to 'cancelled' in-memory; caller must commit."""
        reminder.status = "cancelled"
