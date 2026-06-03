"""Ticketmaster Discovery API — public-API source (key from settings, never hard-coded).

Queries the Discovery v2 events endpoint for a country. The API key is read from
``settings.ticketmaster_api_key``; with no key the scraper disables itself (returns []).

NOTE (verified live 2026-05): Ticketmaster currently has **no Bulgarian inventory**
(`countryCode=BG` → 0 events), so against the project's Sofia focus this source returns
nothing today. The integration is correct and returns events for any populated region; the
parser is verified against a real populated response (fixture in tests/fixtures/).
"""

from __future__ import annotations

from typing import Any

from ingestion.config import settings
from ingestion.domain.models import RawEvent
from ingestion.logging import get_logger
from ingestion.scrapers.base import BaseScraper
from ingestion.scrapers.factory import ScraperFactory

logger = get_logger(__name__)

_API_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
_COUNTRY = "BG"
_PAGE_SIZE = 200

# Ticketmaster classification segment -> our category slug.
_SEGMENT_TO_CATEGORY = {
    "Music": "music",
    "Sports": "sport",
    "Arts & Theatre": "theatre",
    "Film": "cinema",
}


@ScraperFactory.register("ticketmaster")
class TicketmasterScraper(BaseScraper):
    source_type = "api"

    async def scrape(self) -> list[RawEvent]:
        if not settings.ticketmaster_api_key:
            logger.warning("ticketmaster_disabled_no_api_key")
            return []
        data = await self._fetch_json(
            _API_URL,
            params={
                "countryCode": _COUNTRY,
                "apikey": settings.ticketmaster_api_key,
                "size": _PAGE_SIZE,
                "sort": "date,asc",
            },
        )
        return self._parse(data)

    def _parse(self, data: Any) -> list[RawEvent]:
        events = data.get("_embedded", {}).get("events", []) if isinstance(data, dict) else []
        return [self._to_raw(e) for e in events]

    @staticmethod
    def _to_raw(event: dict[str, Any]) -> RawEvent:
        start = event.get("dates", {}).get("start", {})
        start_raw = start.get("dateTime") or start.get("localDate")

        venues = event.get("_embedded", {}).get("venues") or [{}]
        venue = venues[0]
        location = venue.get("location") or {}

        classifications = event.get("classifications") or [{}]
        segment = (classifications[0].get("segment") or {}).get("name")

        return RawEvent(
            source="ticketmaster",
            external_id=str(event.get("id")),
            title=event.get("name"),
            url=event.get("url"),
            start_raw=start_raw,
            venue_name=venue.get("name"),
            venue_city=(venue.get("city") or {}).get("name"),
            category_hint=_SEGMENT_TO_CATEGORY.get(segment) if segment else None,
            raw_payload={
                "id": event.get("id"),
                "lat": location.get("latitude"),
                "lon": location.get("longitude"),
                "segment": segment,
            },
        )
