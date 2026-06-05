"""Authentication service.

Owns all credential and session logic:
  - register: hash password (bcrypt), create user + default preferences
  - login: verify credentials, issue opaque token, persist SHA-256 hash only
  - list_sessions: delegate to SessionRepository

The plain token is returned to the caller exactly once (at login) and never stored;
only its SHA-256 hex digest lives in the DB. This means a leaked DB cannot be used
to replay sessions.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt

from api.config import settings
from api.db.models.users import Session, User, UserPreferences
from api.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from api.repository.sessions import SessionRepository
from api.repository.users import UserRepository


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def register(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        if await self._user_repo.get_by_email(email) is not None:
            raise UserAlreadyExistsError(email)
        # bcrypt silently truncates at 72 bytes; reject rather than accept broken equality.
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        pw_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt(rounds=settings.bcrypt_rounds),
        ).decode()
        user = User(email=email, password_hash=pw_hash, display_name=display_name)
        user = await self._user_repo.add(user)
        await self._user_repo.add_preferences(UserPreferences(user_id=user.id))
        return user

    async def login(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
    ) -> tuple[str, datetime]:
        user = await self._user_repo.get_by_email(email)
        if user is None or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise InvalidCredentialsError("Invalid email or password")
        token = secrets.token_urlsafe(settings.session_token_bytes)
        expires_at = datetime.now(UTC) + timedelta(hours=settings.session_token_ttl_hours)
        session = Session(
            user_id=user.id,
            token_hash=_sha256(token),
            expires_at=expires_at,
            user_agent=user_agent,
        )
        await self._session_repo.add(session)
        return token, expires_at

    async def list_sessions(self, user_id: int) -> list[Session]:
        return await self._session_repo.list_by_user(user_id)
