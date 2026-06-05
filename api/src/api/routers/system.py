"""System endpoints: liveness/readiness checks.

``/health`` performs a trivial ``SELECT 1`` against both databases this service depends on.
``/metrics`` is wired in Phase 9.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from api.db.events import events_session
from api.db.users import users_session

router = APIRouter(tags=["system"])


async def _ping(session_factory: Any) -> str:
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "healthy"
    except Exception:  # noqa: BLE001 - report status without leaking internals
        return "unhealthy"


@router.get("/health")
async def health() -> dict[str, Any]:
    """Report liveness and per-database connectivity."""
    databases = {
        "events": await _ping(events_session),
        "users": await _ping(users_session),
    }
    status = "ok" if all(v == "healthy" for v in databases.values()) else "degraded"
    return {"status": status, "databases": databases}
