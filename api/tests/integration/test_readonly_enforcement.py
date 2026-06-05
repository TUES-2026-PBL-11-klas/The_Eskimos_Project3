"""Integration test: read-only boundary on the events database.

Uses ``SET ROLE events_api`` on a superuser connection to adopt the SELECT-only role,
then proves that an INSERT is refused. This mirrors production where ``EVENTS_DB_URL``
uses the ``events_api`` login (inherits ``events_reader``) — the API cannot accidentally
mutate the events schema regardless of code bugs.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.integration
async def test_events_api_role_cannot_insert(seeded_events_db_url: str) -> None:
    """INSERT is refused when the session runs as events_api (SELECT-only)."""
    engine = create_async_engine(seeded_events_db_url)
    try:
        async with engine.connect() as conn:
            # Adopt the read-only role; superuser connection allows this without re-auth.
            await conn.execute(text("SET ROLE events_api"))
            with pytest.raises(ProgrammingError):
                await conn.execute(
                    text("INSERT INTO sources (name, type) VALUES ('rw_probe', 'api')")
                )
    finally:
        await engine.dispose()


@pytest.mark.integration
async def test_events_api_role_can_select(seeded_events_db_url: str) -> None:
    """SELECT succeeds for events_api — confirms the role is functional, just restricted."""
    engine = create_async_engine(seeded_events_db_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET ROLE events_api"))
            result = await conn.execute(text("SELECT count(*) FROM events"))
            count = result.scalar_one()
            assert isinstance(count, int)
            assert count > 0
    finally:
        await engine.dispose()
