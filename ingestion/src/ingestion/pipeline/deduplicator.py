"""Deduplicator step — collapses duplicate events by `dedup_key`.

Two layers: an in-batch ``set``/dict of seen keys (cross-source dupes within one run) and
``EventRepository.find_duplicate`` (dupes already persisted from a prior run). When a
duplicate is found the record is dropped (return ``None``); for in-batch dupes, missing
fields on the kept record are filled from the newer one first.
"""

from __future__ import annotations

from ingestion.domain.models import NormalizedEvent
from ingestion.metrics import Metrics
from ingestion.pipeline.base import PipelineEvent, PipelineStep
from ingestion.repository.event_repository import EventRepository

_MERGE_FIELDS = (
    "description",
    "venue_name",
    "venue_city",
)


class Deduplicator(PipelineStep):
    def __init__(self, repo: EventRepository, metrics: Metrics | None = None) -> None:
        self._repo = repo
        self._metrics = metrics
        self._seen: dict[str, NormalizedEvent] = {}

    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        if not isinstance(event, NormalizedEvent):
            return event

        kept = self._seen.get(event.dedup_key)
        if kept is not None:
            self._merge(kept, event)  # enrich the already-kept event, drop this one
            self._count()
            return None

        if await self._repo.find_duplicate(event) is not None:
            # Already persisted (e.g. a prior run); upsert would refresh it — drop the new one.
            self._count()
            return None

        self._seen[event.dedup_key] = event
        return event

    @staticmethod
    def _merge(kept: NormalizedEvent, new: NormalizedEvent) -> None:
        for field in _MERGE_FIELDS:
            if getattr(kept, field) is None and getattr(new, field) is not None:
                setattr(kept, field, getattr(new, field))
        alternates = kept.raw_payload.setdefault("alternate_sources", [])
        alternates.append({"source": new.source, "url": new.url})

    def _count(self) -> None:
        if self._metrics is not None:
            self._metrics.deduplicated()
