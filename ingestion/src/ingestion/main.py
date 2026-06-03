"""Worker entrypoint — one full ingestion pass, then exit.

Ties everything together as a producer/consumer pipeline:

    scrapers (parallel, rate-limited)  ──put──▶  asyncio.Queue  ──get──▶  pipeline  ──▶  upsert
       asyncio.gather + Semaphore           bounded (backpressure)     run_one        single tx

Run with ``python -m ingestion.main``. A single failing scraper is logged and skipped — it
never aborts the run. The whole batch persists in one transaction (commit on success,
rollback on any error), and a structured metrics line is logged at the end.
"""

from __future__ import annotations

import asyncio
from collections import Counter, deque
from functools import reduce

import httpx

import ingestion.scrapers  # noqa: F401  (registers scrapers with the factory)
from ingestion.config import settings
from ingestion.db.base import session_scope
from ingestion.domain.models import NormalizedEvent, RawEvent
from ingestion.exceptions import InvalidEventDataError, ScrapingError
from ingestion.logging import configure_logging, get_logger
from ingestion.metrics import Metrics
from ingestion.pipeline.base import Pipeline
from ingestion.pipeline.categorizer import Categorizer
from ingestion.pipeline.deduplicator import Deduplicator
from ingestion.pipeline.normalizer import Normalizer
from ingestion.pipeline.validator import Validator
from ingestion.repository.event_repository import EventRepository
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

logger = get_logger(__name__)

_USER_AGENT = "EventHubBot/1.0 (+https://github.com/eskimos/eventhub; contact@example.com)"
_QUEUE_MAXSIZE = 1000


class _Sentinel:
    """Marks end-of-stream on the queue once all producers are done."""


_SENTINEL = _Sentinel()


async def run() -> None:
    configure_logging()
    metrics = Metrics()
    queue: asyncio.Queue[RawEvent | _Sentinel] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
    semaphore = asyncio.Semaphore(settings.scrape_max_concurrency)
    sources = settings.enabled_sources or ScraperFactory.available()
    logger.info("ingestion_run_start", sources=sources)

    async with httpx.AsyncClient(headers={"User-Agent": _USER_AGENT}) as client:
        scrapers = [ScraperFactory.create(name, client, semaphore) for name in sources]

        async def produce(scraper: BaseScraper) -> None:
            try:
                raws = await scraper.scrape()
            except ScrapingError as exc:
                # One source failing must not abort the run.
                logger.warning("scraper_failed", source=scraper.source_name, error=str(exc))
                return
            for raw in raws:
                metrics.scraped(scraper.source_name)
                await queue.put(raw)  # blocks when full → backpressure

        async def consume(pipeline: Pipeline) -> deque[NormalizedEvent]:
            out: deque[NormalizedEvent] = deque()
            while True:
                item = await queue.get()
                try:
                    if isinstance(item, _Sentinel):
                        break
                    try:
                        event = await pipeline.run_one(item)
                        if event is not None:
                            out.append(event)
                    except InvalidEventDataError as exc:
                        metrics.invalid()
                        logger.debug("event_dropped_invalid", error=str(exc))
                finally:
                    queue.task_done()
            return out

        async with session_scope() as session:  # one transaction for the whole batch
            repo = EventRepository(session)
            pipeline = Pipeline(
                [Validator(), Normalizer(metrics), Deduplicator(repo, metrics), Categorizer()]
            )
            consumer = asyncio.create_task(consume(pipeline))
            await asyncio.gather(*(produce(s) for s in scrapers))  # parallel producers
            await queue.put(_SENTINEL)
            events = await consumer

            for event in events:
                await repo.upsert(event)
            await _mark_sources_run(repo, sources)
            # commit happens on context exit; any error rolls back the whole batch

    _log_category_breakdown(events)
    metrics.log_summary()


async def _mark_sources_run(repo: EventRepository, sources: list[str]) -> None:
    """Stamp last_run_at on the source rows that exist (created during upsert)."""
    await repo.touch_sources_last_run(sources)


def _log_category_breakdown(events: deque[NormalizedEvent]) -> None:
    initial: Counter[str] = Counter()
    counts = reduce(
        lambda acc, event: acc + Counter({event.category.value: 1}),
        events,
        initial,
    )
    logger.info("events_by_category", **dict(counts))


if __name__ == "__main__":
    asyncio.run(run())
