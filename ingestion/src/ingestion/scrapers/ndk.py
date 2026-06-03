"""NDK ticketing — tickets.ndk.bg (HTML, static, JS-free, no anti-bot).

Selectors verified against live markup (2026-05; fixture: tests/fixtures/ndk_list.html).
The all-events page lists `.eventEntryLong` blocks; each carries the date
(`.eventEntryLongLeftDate`, e.g. "31 MAY 2026"), the title (`.eventEntryLongRight`), and an
event id embedded in the left panel's background-image (`event_bg/<id>_preview.jpg`). The
"buy" buttons are JS, but the id maps to a real detail URL: npc_ws_pg_eventinfo.php?event=<id>.
All events are at the National Palace of Culture in Sofia.
"""

from __future__ import annotations

import hashlib
import re

from bs4 import BeautifulSoup

from ingestion.domain.models import RawEvent
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

_LIST_URL = "https://www.tickets.ndk.bg/npc_ws_pg_allevents.php"
_DETAIL_URL = "https://www.tickets.ndk.bg/npc_ws_pg_eventinfo.php?event={eid}"
_ID_RE = re.compile(r"event_bg/(\d+)")


@ScraperFactory.register("ndk")
class NdkScraper(BaseScraper):
    source_type = "scraper"

    async def scrape(self) -> list[RawEvent]:
        html = await self._fetch_text(_LIST_URL)
        return self._parse(html)

    def _parse(self, html: str) -> list[RawEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawEvent] = []
        for el in soup.select(".eventEntryLong"):
            left = el.select_one(".eventEntryLongLeft")
            right = el.select_one(".eventEntryLongRight")
            date_el = el.select_one(".eventEntryLongLeftDate")
            if left is None or right is None or date_el is None:
                continue

            title = right.get_text(" ", strip=True)
            date_text = date_el.get_text(" ", strip=True)
            eid = self._event_id(left.get("style"), title, date_text)
            events.append(
                RawEvent(
                    source="ndk",
                    external_id=eid,
                    title=title,
                    url=_DETAIL_URL.format(eid=eid),
                    start_raw=date_text,
                    venue_name="National Palace of Culture (NDK)",
                    venue_city="Sofia",
                    raw_payload={"date_text": date_text},
                )
            )
        return events

    @staticmethod
    def _event_id(style: object, title: str, date_text: str) -> str:
        if isinstance(style, str):
            match = _ID_RE.search(style)
            if match:
                return match.group(1)
        # Fallback: stable hash of title + date when no id is present.
        digest = hashlib.sha1(f"{title}|{date_text}".encode()).hexdigest()
        return f"h{digest[:16]}"
