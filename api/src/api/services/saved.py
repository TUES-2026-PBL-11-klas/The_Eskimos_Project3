"""Saved-events service.

Bridges the read-only events DB and the read-write users DB:
  - save: fetches event snapshot from events DB, persists into saved_events
  - unsave: ownership-checked deletion (cascades reminders via DB FK)
  - list_saved: delegates to repository, ordered by start_at
  - calendar: groups saved events by UTC calendar day over a date window
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from api.db.models.users import SavedEvent
from api.domain.exceptions import AlreadySavedError, EventNotFoundError
from api.repository.events import EventRepository
from api.repository.saved import SavedEventRepository
from api.schemas.saved import SavedEventSchema


class SavedEventService:
    def __init__(
        self,
        event_repo: EventRepository,
        saved_repo: SavedEventRepository,
    ) -> None:
        self._event_repo = event_repo
        self._saved_repo = saved_repo

    async def save(self, user_id: int, event_id: int) -> SavedEventSchema:
        event = await self._event_repo.get(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        source_name = event.source.name if event.source else "unknown"
        existing = await self._saved_repo.get_by_source_external_id(
            user_id, source_name, event.external_id
        )
        if existing is not None:
            raise AlreadySavedError(source_name, event.external_id)
        saved = SavedEvent(
            user_id=user_id,
            source=source_name,
            external_id=event.external_id,
            event_id=event.id,
            title=event.title,
            start_at=event.start_at,
            venue_name=event.venue.name if event.venue else None,
            city=event.venue.city if event.venue else None,
            category=event.category.name if event.category else None,
            url=event.url,
        )
        orm_saved = await self._saved_repo.add(saved)
        return SavedEventSchema.model_validate(orm_saved)

    async def unsave(self, user_id: int, saved_id: int) -> None:
        se = await self._saved_repo.get_for_user(saved_id, user_id)
        if se is None:
            # get_for_user returns None for both missing rows and ownership violations.
            raise EventNotFoundError(saved_id)
        await self._saved_repo.delete(se)

    async def list_saved(self, user_id: int) -> list[SavedEventSchema]:
        events = await self._saved_repo.list_by_user(user_id)
        return [SavedEventSchema.model_validate(e) for e in events]

    async def calendar(
        self, user_id: int, from_dt: datetime, to_dt: datetime
    ) -> dict[str, list[SavedEventSchema]]:
        """Return saved events in [from_dt, to_dt] grouped by UTC calendar day (sorted)."""
        events = await self._saved_repo.list_by_user_in_range(user_id, from_dt, to_dt)
        groups: dict[str, list[SavedEventSchema]] = defaultdict(list)
        for se in events:
            day = se.start_at.astimezone(UTC).date().isoformat()
            groups[day].append(SavedEventSchema.model_validate(se))
        return dict(sorted(groups.items()))
