"""Repository for the ``sessions`` table (opaque bearer-token records)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models.users import Session
from api.repository.base import AsyncRepository


class SessionRepository(AsyncRepository[Session]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: int) -> Session | None:
        result = await self._session.execute(select(Session).where(Session.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        result = await self._session.execute(
            select(Session).where(Session.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Session]:
        result = await self._session.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
        )
        return list(result.scalars())

    async def add(self, session: Session) -> Session:
        """Persist a new session record and flush so ``session.id`` is populated."""
        self._session.add(session)
        await self._session.flush()
        return session

    async def delete(self, session: Session) -> None:
        """Mark the session for deletion; caller must commit."""
        await self._session.delete(session)
