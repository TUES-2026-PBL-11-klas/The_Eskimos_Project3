"""In-process metrics — a stand-in for Prometheus.

A small class wrapping ``collections.Counter``; the orchestrator emits a single structured
log line at the end of a run via :meth:`Metrics.log_summary`.
"""

from __future__ import annotations

import time
from collections import Counter

from ingestion.logging import get_logger

logger = get_logger(__name__)


class Metrics:
    def __init__(self) -> None:
        self._scraped: Counter[str] = Counter()  # per-source scrape counts
        self._normalized = 0
        self._deduplicated = 0
        self._invalid = 0
        self._start = time.perf_counter()

    def scraped(self, source: str) -> None:
        self._scraped[source] += 1

    def normalized(self) -> None:
        self._normalized += 1

    def deduplicated(self) -> None:
        self._deduplicated += 1

    def invalid(self) -> None:
        self._invalid += 1

    @property
    def pipeline_duration_seconds(self) -> float:
        return time.perf_counter() - self._start

    def log_summary(self) -> None:
        logger.info(
            "ingestion_run_complete",
            events_scraped_total=dict(self._scraped),
            events_scraped_grand_total=sum(self._scraped.values()),
            events_normalized_total=self._normalized,
            events_deduplicated_total=self._deduplicated,
            events_invalid_total=self._invalid,
            pipeline_duration_seconds=round(self.pipeline_duration_seconds, 3),
        )
