"""VisitSofia — visitsofia.bg municipal events portal (HTML, Joomla JEvents).

Selectors verified against live markup (2026-05; fixture: tests/fixtures/visitsofia_calendar.html).
The JEvents list at /bg/component/jevents/month.calendar renders `.jev_list_desc_container`
blocks; each detail link embeds the date and event id
(icalrepeat.detail/YYYY/MM/DD/<id>/). Events repeat across the page, so we de-dupe by
(id, date). robots.txt disallows /components/ (plural); this SEF route is /component/ (allowed).
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ingestion.domain.models import RawEvent
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

_LIST_URL = "https://www.visitsofia.bg/bg/component/jevents/month.calendar"
_DETAIL_RE = re.compile(r"icalrepeat\.detail/(\d{4})/(\d{2})/(\d{2})/(\d+)")
_DETAIL_URL = (
    "https://www.visitsofia.bg/bg/component/jevents/icalrepeat.detail/{y}/{m}/{d}/{eid}/-/"
)


@ScraperFactory.register("visitsofia")
class VisitSofiaScraper(BaseScraper):
    source_type = "scraper"

    async def scrape(self) -> list[RawEvent]:
        html = await self._fetch_text(_LIST_URL)
        return self._parse(html)

    def _parse(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[tuple[str, str]] = set()
        events: list[RawEvent] = []
        for container in soup.select(".jev_list_desc_container"):
            link = container.select_one(".jev_list_title a[href]")
            href = link.get("href") if link else None
            if link is None or not isinstance(href, str):
                continue
            match = _DETAIL_RE.search(href)
            if match is None:
                continue
            year, month, day, eid = match.groups()
            key = (eid, f"{year}{month}{day}")
            if key in seen:
                continue
            seen.add(key)

            desc = container.select_one(".jev_list_desc")
            events.append(
                RawEvent(
                    source="visitsofia",
                    external_id=f"{eid}-{year}{month}{day}",
                    title=link.get_text(" ", strip=True),
                    url=_DETAIL_URL.format(y=year, m=month, d=day, eid=eid),
                    start_raw=f"{year}-{month}-{day}",
                    description=desc.get_text(" ", strip=True) if desc else None,
                    venue_city="Sofia",
                    raw_payload={"event_id": eid, "date": f"{year}-{month}-{day}"},
                )
            )
        return events
