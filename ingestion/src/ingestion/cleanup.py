"""Retention worker — prune events that have already passed.

A one-shot batch sibling to ``main.py``: computes a cutoff of ``now - cleanup_grace_days``,
deletes events whose ``start_at`` is before it, and logs a summary. Intended to run weekly
in production (the scheduler itself is out of scope).
Run with ``python -m ingestion.cleanup``.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta

from ingestion.config import settings
from ingestion.db.base import session_scope
from ingestion.logging import configure_logging, get_logger
from ingestion.repository.event_repository import EventRepository

logger = get_logger(__name__)


async def run() -> None:
    configure_logging()
    cutoff = datetime.now(UTC) - timedelta(days=settings.cleanup_grace_days)
    started = time.perf_counter()

    async with session_scope() as session:
        pruned = await EventRepository(session).delete_past(cutoff)

    logger.info(
        "cleanup_run_complete",
        events_pruned_total=pruned,
        cutoff=cutoff.isoformat(),
        grace_days=settings.cleanup_grace_days,
        duration_seconds=round(time.perf_counter() - started, 3),
    )


if __name__ == "__main__":
    asyncio.run(run())
