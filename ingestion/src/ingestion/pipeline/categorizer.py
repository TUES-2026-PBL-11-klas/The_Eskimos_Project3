"""Categorizer step — classifies an event via the keyword map.

Order of precedence: keyword match over title+description → the source's category hint
(already seeded onto `category` by the Normalizer) → ``UNCATEGORIZED``. Uses comprehensions
+ ``sorted(key=lambda ...)`` (functional/stream style) to rank categories by keyword hits.
"""

from __future__ import annotations

from ingestion.domain.categories import KEYWORD_MAP, Category
from ingestion.domain.models import NormalizedEvent
from ingestion.pipeline.base import PipelineEvent, PipelineStep


class Categorizer(PipelineStep):
    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        if not isinstance(event, NormalizedEvent):
            return event
        matched = self._classify(event)
        if matched is not None:
            event.category = matched  # keyword win; else keep the hint/UNCATEGORIZED
        return event

    @staticmethod
    def _classify(event: NormalizedEvent) -> Category | None:
        text = f"{event.title} {event.description or ''}".lower()
        scores = {
            category: sum(1 for keyword in keywords if keyword in text)
            for category, keywords in KEYWORD_MAP.items()
        }
        best_category, best_score = max(scores.items(), key=lambda item: item[1])
        return best_category if best_score > 0 else None
