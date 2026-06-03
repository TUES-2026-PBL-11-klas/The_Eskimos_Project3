"""Factory + registry for scrapers (Factory pattern + Open/Closed Principle).

Each scraper module registers itself with ``@ScraperFactory.register("name")``. Adding a new
source is a new registered class with zero changes to the pipeline or orchestrator.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from ingestion.exceptions import ScrapingError
from ingestion.scrapers.base import BaseScraper


class ScraperFactory:
    _registry: dict[str, type[BaseScraper]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[BaseScraper]], type[BaseScraper]]:
        def decorator(scraper_cls: type[BaseScraper]) -> type[BaseScraper]:
            scraper_cls.source_name = name
            cls._registry[name] = scraper_cls
            return scraper_cls

        return decorator

    @classmethod
    def create(
        cls, name: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore
    ) -> BaseScraper:
        try:
            return cls._registry[name](client, semaphore)
        except KeyError as exc:
            raise ScrapingError(f"unknown source: {name}") from exc

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)
