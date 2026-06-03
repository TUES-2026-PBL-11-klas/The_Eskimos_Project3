"""dev.bg — tech/business events (HTML, The Events Calendar plugin).

Selectors verified against live markup (2026-05; fixture: tests/fixtures/devbg_list.html).
The /events/ page renders server-side "mobile month" event blocks with a clean structure:
title-link, datetime text, and price. Scrapers emit raw strings only — the Normalizer
(Phase 4) parses the Bulgarian datetime ("27 април @ 7:30 pm - 8:40 pm EEST") to UTC.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from ingestion.domain.models import RawEvent
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

_LIST_URL = "https://dev.bg/events/"
_P = "tribe-events-calendar-month-mobile-events__mobile-event"
_FEATURED_PREFIX = re.compile(r"^\s*Featured\s*", re.IGNORECASE)


@ScraperFactory.register("devbg")
class DevBgScraper(BaseScraper):
    source_type = "scraper"

    async def scrape(self) -> list[RawEvent]:
        html = await self._fetch_text(_LIST_URL)
        return self._parse(html)

    def _parse(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawEvent] = []
        for el in soup.select(f"article.{_P}, div.{_P}"):
            link = el.select_one(f"a.{_P}-title-link")
            title_el = el.select_one(f".{_P}-title")
            if link is None or title_el is None:
                continue
            href = link.get("href")
            if not isinstance(href, str) or not href:
                continue

            datetime_el = el.select_one(f".{_P}-datetime")
            when = self._clean(datetime_el)
            events.append(
                RawEvent(
                    source="devbg",
                    external_id=self._external_id(href),
                    title=title_el.get_text(" ", strip=True),
                    url=href,
                    start_raw=when,
                    # dev.bg = tech/business meetups → education bucket fallback.
                    category_hint="education",
                    raw_payload={"datetime_text": when},
                )
            )
        return events

    @staticmethod
    def _clean(el: Tag | None) -> str | None:
        if el is None:
            return None
        text = _FEATURED_PREFIX.sub("", el.get_text(" ", strip=True)).strip()
        return text or None

    @staticmethod
    def _external_id(url: str) -> str:
        slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        return slug or url
