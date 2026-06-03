"""PipelineStep (Chain of Responsibility) + Pipeline (composition).

A `RawEvent` flows through ordered steps; each `process` returns the (possibly transformed)
event or ``None`` to drop it. The chain transforms `RawEvent` → `NormalizedEvent`, so steps
accept the union of both and narrow internally.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ingestion.domain.models import NormalizedEvent, RawEvent
from ingestion.exceptions import EventHubError

PipelineEvent = RawEvent | NormalizedEvent


class PipelineStep(ABC):
    @abstractmethod
    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        """Transform the event, or return None to drop it from the batch."""


class Pipeline:
    def __init__(self, steps: list[PipelineStep]) -> None:
        self._steps = steps

    async def run_one(self, raw: RawEvent) -> NormalizedEvent | None:
        event: PipelineEvent = raw
        for step in self._steps:
            result = await step.process(event)
            if result is None:
                return None  # a step dropped it (invalid / duplicate)
            event = result
        if not isinstance(event, NormalizedEvent):
            # Misconfigured pipeline (e.g. no Normalizer) — fail loud, don't persist a RawEvent.
            raise EventHubError("pipeline did not produce a NormalizedEvent")
        return event
