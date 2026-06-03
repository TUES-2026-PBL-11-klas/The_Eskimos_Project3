"""Validator step — drops events missing required raw fields.

Operates on the `RawEvent`. On failure it raises `InvalidEventDataError`; the consumer
catches it per-event, counts `events_invalid_total`, and continues — one bad event must
not kill the batch.
"""

from __future__ import annotations

from ingestion.domain.models import RawEvent
from ingestion.exceptions import InvalidEventDataError
from ingestion.pipeline.base import PipelineEvent, PipelineStep

# `source` is guaranteed by the RawEvent model; these three are the droppable ones.
_REQUIRED = ("title", "start_raw", "url")


class Validator(PipelineStep):
    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        if not isinstance(event, RawEvent):
            return event
        missing = [field for field in _REQUIRED if not getattr(event, field)]
        if missing:
            raise InvalidEventDataError(
                f"{event.source}: event missing required field(s): {', '.join(missing)}"
            )
        return event
