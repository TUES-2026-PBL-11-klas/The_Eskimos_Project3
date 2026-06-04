"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.events import events_session
from api.repository.events import EventRepository
from api.services.events import EventService


async def _get_events_session() -> AsyncIterator[AsyncSession]:
    async with events_session() as session:
        yield session


_EventsSessionDep = Annotated[AsyncSession, Depends(_get_events_session)]


def get_event_repository(session: _EventsSessionDep) -> EventRepository:
    return EventRepository(session)


EventRepositoryDep = Annotated[EventRepository, Depends(get_event_repository)]


def get_event_service(repo: EventRepositoryDep) -> EventService:
    return EventService(repo)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
