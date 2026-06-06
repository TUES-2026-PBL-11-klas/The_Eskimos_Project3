"""PastEventFilter step — drops events whose start time is already in the past.

Uses the same grace-period threshold as the cleanup worker so the two are consistent:
events older than ``now - cleanup_grace_days`` are silently dropped rather than upserted.
This prevents the hourly ingestion run from re-inserting events that the daily cleanup
already deleted (or would delete).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ingestion.config import settings
from ingestion.domain.models import NormalizedEvent
from ingestion.logging import get_logger
from ingestion.pipeline.base import PipelineEvent, PipelineStep

logger = get_logger(__name__)


class PastEventFilter(PipelineStep):
    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        if not isinstance(event, NormalizedEvent):
            return event
        cutoff = datetime.now(UTC) - timedelta(days=settings.cleanup_grace_days)
        if event.start_at < cutoff:
            logger.debug(
                "event_dropped_past",
                title=event.title,
                start_at=event.start_at.isoformat(),
                cutoff=cutoff.isoformat(),
            )
            return None
        return event
