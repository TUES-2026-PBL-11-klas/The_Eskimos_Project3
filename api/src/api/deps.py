"""FastAPI dependency providers."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.events import events_session
from api.db.models.users import Session as OrmSession
from api.db.models.users import User
from api.db.users import users_session
from api.repository.events import EventRepository
from api.repository.reminders import ReminderRepository
from api.repository.saved import SavedEventRepository
from api.repository.sessions import SessionRepository
from api.repository.users import UserRepository
from api.services.auth import AuthService
from api.services.events import EventService
from api.services.me import MeService
from api.services.reminders import ReminderService
from api.services.saved import SavedEventService

# ── events DB (read-only) ────────────────────────────────────────────────────


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


# ── users DB (read-write) ────────────────────────────────────────────────────


async def _get_users_session() -> AsyncIterator[AsyncSession]:
    async with users_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


_UsersSessionDep = Annotated[AsyncSession, Depends(_get_users_session)]


def get_user_repository(session: _UsersSessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_session_repository(session: _UsersSessionDep) -> SessionRepository:
    return SessionRepository(session)


SessionRepositoryDep = Annotated[SessionRepository, Depends(get_session_repository)]


def get_saved_event_repository(session: _UsersSessionDep) -> SavedEventRepository:
    return SavedEventRepository(session)


SavedEventRepositoryDep = Annotated[SavedEventRepository, Depends(get_saved_event_repository)]


def get_reminder_repository(session: _UsersSessionDep) -> ReminderRepository:
    return ReminderRepository(session)


ReminderRepositoryDep = Annotated[ReminderRepository, Depends(get_reminder_repository)]


def get_auth_service(
    user_repo: UserRepositoryDep,
    session_repo: SessionRepositoryDep,
) -> AuthService:
    return AuthService(user_repo, session_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_saved_event_service(
    event_repo: EventRepositoryDep,
    saved_repo: SavedEventRepositoryDep,
) -> SavedEventService:
    return SavedEventService(event_repo, saved_repo)


SavedEventServiceDep = Annotated[SavedEventService, Depends(get_saved_event_service)]


def get_reminder_service(
    saved_repo: SavedEventRepositoryDep,
    reminder_repo: ReminderRepositoryDep,
    user_repo: UserRepositoryDep,
) -> ReminderService:
    return ReminderService(saved_repo, reminder_repo, user_repo)


ReminderServiceDep = Annotated[ReminderService, Depends(get_reminder_service)]


def get_me_service(user_repo: UserRepositoryDep) -> MeService:
    return MeService(user_repo)


MeServiceDep = Annotated[MeService, Depends(get_me_service)]


# ── current session / user (bearer token validation) ─────────────────────────


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _get_current_session(
    request: Request,
    session_repo: SessionRepositoryDep,
) -> OrmSession:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_hash = _sha256(auth[7:])
    db_sess = await session_repo.get_by_token_hash(token_hash)
    if db_sess is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if db_sess.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Session expired")
    return db_sess


CurrentSessionDep = Annotated[OrmSession, Depends(_get_current_session)]


async def _get_current_user(
    db_sess: CurrentSessionDep,
    user_repo: UserRepositoryDep,
) -> User:
    user = await user_repo.get(db_sess.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User account not found")
    return user


CurrentUserDep = Annotated[User, Depends(_get_current_user)]
