"""Read-write repository for the ``users`` table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models.users import User, UserPreferences
from api.repository.base import AsyncRepository


class UserRepository(AsyncRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        """Persist a new user and flush so ``user.id`` is populated before commit."""
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_preferences(self, user_id: int) -> UserPreferences | None:
        result = await self._session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_preferences(self, prefs: UserPreferences) -> None:
        """Stage default preferences for a user; caller flushes/commits."""
        self._session.add(prefs)
