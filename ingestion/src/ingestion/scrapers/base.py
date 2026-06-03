"""Strategy base class for all sources.

Every source — public API or HTML scraper — is a ``BaseScraper`` subclass implementing
``scrape() -> list[RawEvent]``. Shared HTTP concerns live in ``_fetch_text`` / ``_fetch_json``:
the ``asyncio.Semaphore`` (shared-resource rate limit) gates outbound concurrency, and
``tenacity`` retries transient failures with exponential backoff before giving up with a
``ScrapingError``.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ingestion.config import settings
from ingestion.domain.models import RawEvent
from ingestion.exceptions import ScrapingError
from ingestion.logging import get_logger

logger = get_logger(__name__)

# Transient HTTP conditions worth retrying.
_RETRYABLE = (httpx.TransportError, httpx.HTTPStatusError)


class BaseScraper(ABC):
    #: Stable identifier; matches the factory registration name and the DB source name.
    source_name: str = ""
    #: "api" or "scraper" — used when a source row is created.
    source_type: str = "scraper"

    def __init__(self, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> None:
        self._client = client
        self._semaphore = semaphore

    @abstractmethod
    async def scrape(self) -> list[RawEvent]:
        """Fetch and parse this source into loosely-typed RawEvents."""

    async def _request(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Semaphore-gated GET with retry/backoff; raises ScrapingError on terminal failure."""
        async with self._semaphore:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=0.5, max=8),
                    retry=retry_if_exception_type(_RETRYABLE),
                    reraise=True,
                ):
                    with attempt:
                        resp = await self._client.get(
                            url,
                            params=params,
                            headers=headers,
                            timeout=settings.http_timeout_seconds,
                        )
                        resp.raise_for_status()
                        return resp
            except httpx.HTTPError as exc:
                raise ScrapingError(f"{self.source_name}: fetch failed for {url}: {exc}") from exc
        # AsyncRetrying with reraise=True always returns or raises inside the loop.
        raise ScrapingError(f"{self.source_name}: exhausted retries for {url}")

    async def _fetch_text(self, url: str, *, params: dict[str, Any] | None = None) -> str:
        resp = await self._request(url, params=params)
        return resp.text

    async def _fetch_json(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        resp = await self._request(url, params=params, headers={"Accept": "application/json"})
        try:
            return resp.json()
        except ValueError as exc:
            raise ScrapingError(f"{self.source_name}: invalid JSON from {url}") from exc
