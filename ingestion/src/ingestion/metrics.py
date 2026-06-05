"""Run metrics — in-process counters plus a Prometheus Pushgateway export.

A small class wrapping ``collections.Counter``; the orchestrator emits a single structured
log line at the end of a run via :meth:`Metrics.log_summary` (the offline fallback) and, when
a gateway is configured, pushes the same numbers to Prometheus via :meth:`Metrics.push`.
"""

from __future__ import annotations

import time
from collections import Counter

from prometheus_client import CollectorRegistry, Gauge
from prometheus_client import Counter as PromCounter
from prometheus_client import push_to_gateway as prom_push_to_gateway

from ingestion.logging import get_logger

logger = get_logger(__name__)

_PUSH_JOB = "ingestion"


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

    def build_registry(self) -> CollectorRegistry:
        """Snapshot this run's counters into a fresh Prometheus registry."""
        registry = CollectorRegistry()
        scraped = PromCounter(
            "events_scraped_total",
            "Total events scraped, per source.",
            ["source"],
            registry=registry,
        )
        for source, count in self._scraped.items():
            scraped.labels(source=source).inc(count)
        PromCounter(
            "events_normalized_total",
            "Total events that passed normalization.",
            registry=registry,
        ).inc(self._normalized)
        PromCounter(
            "events_deduplicated_total",
            "Total events dropped as duplicates.",
            registry=registry,
        ).inc(self._deduplicated)
        Gauge(
            "pipeline_duration_seconds",
            "Wall-clock duration of the ingestion pipeline.",
            registry=registry,
        ).set(self.pipeline_duration_seconds)
        return registry

    def push(self, gateway_url: str, *, job: str = _PUSH_JOB) -> None:
        """Best-effort push of run metrics to a Prometheus Pushgateway.

        Ingestion is a one-shot job, so Prometheus' pull model can't scrape it after it
        exits — we push instead. A gateway outage must never fail the run: any error is
        logged and swallowed, and the structlog summary line remains the offline fallback.
        """
        try:
            prom_push_to_gateway(gateway_url, job=job, registry=self.build_registry())
        except Exception as exc:
            logger.warning("metrics_push_failed", gateway=gateway_url, error=str(exc))
        else:
            logger.info("metrics_pushed", gateway=gateway_url, job=job)
