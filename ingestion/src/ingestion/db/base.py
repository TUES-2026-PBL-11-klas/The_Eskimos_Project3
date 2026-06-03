"""Async engine, session factory, and the single-transaction `session_scope()`.

The orchestrator (Phase 5) wraps an entire ingestion pass in one `session_scope()` so the
whole batch commits atomically or rolls back on any error.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ingestion.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# expire_on_commit=False so objects stay usable after the transaction commits.
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield a session inside a single transaction.

    `session.begin()` commits on clean exit and rolls back if the body raises —
    giving the all-or-nothing batch semantics the worker relies on.
    """
    async with async_session_factory() as session, session.begin():
        yield session
