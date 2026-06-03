"""Normalizer step — turns a RawEvent into a persistable NormalizedEvent.

Responsibilities: strip HTML from the description, parse the raw date string to a UTC
datetime (Bulgarian/English month names, ISO, am/pm; source tz = Europe/Sofia), collapse
whitespace in the title, seed the category from the source hint, and compute the
deterministic `dedup_key`.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from slugify import slugify

from ingestion.domain.categories import Category
from ingestion.domain.models import NormalizedEvent, RawEvent
from ingestion.exceptions import InvalidEventDataError
from ingestion.metrics import Metrics
from ingestion.pipeline.base import PipelineEvent, PipelineStep

_SOFIA = ZoneInfo("Europe/Sofia")

# Bulgarian month names (full + common 3-letter abbreviations) → English, for dateutil.
_BG_MONTHS = {
    "януари": "January",
    "февруари": "February",
    "март": "March",
    "април": "April",
    "май": "May",
    "юни": "June",
    "юли": "July",
    "август": "August",
    "септември": "September",
    "октомври": "October",
    "ноември": "November",
    "декември": "December",
    "ян": "January",
    "фев": "February",
    "мар": "March",
    "апр": "April",
    "авг": "August",
    "сеп": "September",
    "окт": "October",
    "ное": "November",
    "дек": "December",
}
_BG_MONTH_RE = re.compile("|".join(sorted(_BG_MONTHS, key=len, reverse=True)), re.IGNORECASE)
_RANGE_SEP = re.compile(r"\s[–-]\s")  # "7:30 pm - 8:40 pm" → take the start
_TZ_ABBR = re.compile(r"\b(EEST|EET)\b")
_YEAR_RE = re.compile(r"\d{4}")


def strip_html(value: str | None) -> str | None:
    if not value:
        return None
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip() or None


def parse_event_datetime(raw: str) -> datetime:
    """Parse a source date string to a timezone-aware UTC datetime."""
    cleaned = _TZ_ABBR.sub("", _RANGE_SEP.split(raw.strip())[0].replace("@", " "))
    cleaned = _BG_MONTH_RE.sub(lambda m: _BG_MONTHS[m.group(0).lower()], cleaned).strip()
    if not cleaned:
        raise ValueError(f"empty date string: {raw!r}")
    parsed = dateutil_parser.parse(cleaned, fuzzy=True)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_SOFIA)
    parsed = parsed.astimezone(UTC)
    # No explicit year in the source → assume the next upcoming occurrence.
    if not _YEAR_RE.search(raw) and parsed < datetime.now(UTC):
        parsed = parsed.replace(year=parsed.year + 1)
    return parsed


def _hint_to_category(hint: str | None) -> Category:
    if hint:
        try:
            return Category(hint.lower())
        except ValueError:
            return Category.UNCATEGORIZED
    return Category.UNCATEGORIZED


def compute_dedup_key(title: str, start_at: datetime, venue_city: str | None) -> str:
    return f"{slugify(title)}|{start_at.date().isoformat()}|{slugify(venue_city or '')}"


class Normalizer(PipelineStep):
    def __init__(self, metrics: Metrics | None = None) -> None:
        self._metrics = metrics

    async def process(self, event: PipelineEvent) -> PipelineEvent | None:
        if not isinstance(event, RawEvent):
            return event
        try:
            start_at = parse_event_datetime(event.start_raw or "")
        except (ValueError, OverflowError, TypeError) as exc:
            raise InvalidEventDataError(
                f"{event.source}: unparseable date {event.start_raw!r}"
            ) from exc

        title = re.sub(r"\s+", " ", event.title or "").strip()
        url = event.url or ""
        normalized = NormalizedEvent(
            source=event.source,
            external_id=event.external_id or hashlib.sha1(url.encode()).hexdigest()[:16],
            title=title,
            description=strip_html(event.description),
            start_at=start_at,
            url=url,
            venue_name=event.venue_name,
            venue_city=event.venue_city,
            category=_hint_to_category(event.category_hint),
            dedup_key=compute_dedup_key(title, start_at, event.venue_city),
            raw_payload=event.raw_payload,
        )
        if self._metrics is not None:
            self._metrics.normalized()
        return normalized
