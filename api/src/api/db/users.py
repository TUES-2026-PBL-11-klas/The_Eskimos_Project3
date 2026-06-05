"""Read-write async engine + session factory for the **users** database.

This service owns the users schema. All authentication, saved events, calendar, and reminder
data lives here. Connection pooling is configured from settings with ``pool_pre_ping=True``
so stale connections are recycled transparently. The engine is opened in the FastAPI lifespan
and disposed on shutdown.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.config import settings

users_engine: AsyncEngine = create_async_engine(
    settings.users_db_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

users_session_factory = async_sessionmaker(users_engine, expire_on_commit=False)


@asynccontextmanager
async def users_session() -> AsyncIterator[AsyncSession]:
    """Yield a read-write session for the users database, released on exit."""
    async with users_session_factory() as session:
        yield session
