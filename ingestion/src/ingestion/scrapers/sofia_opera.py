"""Sofia Opera and Ballet — operasofia.bg (HTML, server-rendered).

Selectors verified against live markup (2026-05; fixture: tests/fixtures/sofia_opera_calendar.html).
The monthly calendar at /calendar/YYYY-MM lists ``.item`` blocks grouped under day headers
(``.day-number``). Each item carries a /repertoire/<id> link, start time, title, and stage.
Year+month come from the URL; the day from the nearest preceding header. Scrapes the current
and next month.
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from ingestion.domain.models import RawEvent
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

_CALENDAR_URL = "https://www.operasofia.bg/calendar/{ym}"
_REPERTOIRE_ID = re.compile(r"/repertoire/(\d+)")
_MONTHS_AHEAD = 2


def _months(count: int) -> list[str]:
    today = date.today()
    year, month = today.year, today.month
    out: list[str] = []
    for _ in range(count):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month, year = 1, year + 1
    return out


@ScraperFactory.register("sofia_opera")
class SofiaOperaScraper(BaseScraper):
    source_type = "scraper"

    async def scrape(self) -> list[RawEvent]:
        events: list[RawEvent] = []
        for ym in _months(_MONTHS_AHEAD):
            html = await self._fetch_text(_CALENDAR_URL.format(ym=ym))
            events.extend(self._parse(html, ym))
        return events

    def _parse(self, html: str, ym: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        year, month = ym.split("-")
        events: list[RawEvent] = []
        for item in soup.select(".item"):
            desc = item.select_one(".item__description")
            link = desc.find("a", href=True) if desc else None
            name = desc.select_one(".item__description__name") if desc else None
            day_el = item.find_previous(class_="day-number")
            if desc is None or link is None or name is None or day_el is None:
                continue
            href = link.get("href")
            day = day_el.get_text(strip=True)
            if not isinstance(href, str) or not day.isdigit():
                continue

            time_el = desc.select_one(".start-time__hour")
            scene = item.select_one(".item__location__scene")
            time_text = time_el.get_text(strip=True) if time_el else "00:00"
            start_raw = f"{year}-{month}-{int(day):02d} {time_text}"
            rid_match = _REPERTOIRE_ID.search(href)
            rid = rid_match.group(1) if rid_match else day

            events.append(
                RawEvent(
                    source="sofia_opera",
                    external_id=f"{rid}-{year}-{month}-{int(day):02d}",
                    title=name.get_text(" ", strip=True),
                    url=href,
                    start_raw=start_raw,
                    venue_name=scene.get_text(" ", strip=True)
                    if scene
                    else "Sofia Opera and Ballet",
                    venue_city="Sofia",
                    # Opera/ballet house → music by default; keywords refine (балет → theatre).
                    category_hint="music",
                    raw_payload={"date": start_raw, "repertoire_id": rid},
                )
            )
        return events
