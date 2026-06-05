"""Repository for the ``saved_events`` table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models.users import SavedEvent
from api.repository.base import AsyncRepository


class SavedEventRepository(AsyncRepository[SavedEvent]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: int) -> SavedEvent | None:
        result = await self._session.execute(select(SavedEvent).where(SavedEvent.id == entity_id))
        return result.scalar_one_or_none()

    async def get_for_user(self, saved_event_id: int, user_id: int) -> SavedEvent | None:
        """Fetch a saved event only if it belongs to the given user (ownership check)."""
        result = await self._session.execute(
            select(SavedEvent).where(
                SavedEvent.id == saved_event_id,
                SavedEvent.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_source_external_id(
        self, user_id: int, source: str, external_id: str
    ) -> SavedEvent | None:
        result = await self._session.execute(
            select(SavedEvent).where(
                SavedEvent.user_id == user_id,
                SavedEvent.source == source,
                SavedEvent.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[SavedEvent]:
        result = await self._session.execute(
            select(SavedEvent).where(SavedEvent.user_id == user_id).order_by(SavedEvent.start_at)
        )
        return list(result.scalars())

    async def add(self, saved_event: SavedEvent) -> SavedEvent:
        """Persist a snapshot and flush so ``saved_event.id`` is populated."""
        self._session.add(saved_event)
        await self._session.flush()
        return saved_event

    async def list_by_user_in_range(
        self, user_id: int, from_dt: datetime, to_dt: datetime
    ) -> list[SavedEvent]:
        result = await self._session.execute(
            select(SavedEvent)
            .where(
                SavedEvent.user_id == user_id,
                SavedEvent.start_at >= from_dt,
                SavedEvent.start_at <= to_dt,
            )
            .order_by(SavedEvent.start_at)
        )
        return list(result.scalars())

    async def delete(self, saved_event: SavedEvent) -> None:
        """Mark for deletion (cascades to reminders); caller must commit."""
        await self._session.delete(saved_event)
