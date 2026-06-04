"""Read-only async engine + session factory for the **events** database.

This service does not own the events schema — the ingestion service is its sole writer. We
attach with a SELECT-only login role in production; the engine here exposes only sessions,
and the repository layer (Phase 2) exposes no write methods. Connection pooling is configured
from settings with ``pool_pre_ping=True`` so stale connections are recycled transparently.
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

events_engine: AsyncEngine = create_async_engine(
    settings.events_db_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

# expire_on_commit=False keeps loaded objects usable after the session closes.
events_session_factory = async_sessionmaker(events_engine, expire_on_commit=False)


@asynccontextmanager
async def events_session() -> AsyncIterator[AsyncSession]:
    """Yield a read-only session for the events database, released on exit."""
    async with events_session_factory() as session:
        yield session
