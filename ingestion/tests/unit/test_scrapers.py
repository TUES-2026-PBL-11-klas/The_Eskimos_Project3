"""Unit tests for scrapers — factory + offline parser tests against recorded fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import ingestion.scrapers  # noqa: F401  (registers scrapers)
from ingestion.exceptions import ScrapingError
from ingestion.scrapers.devbg import DevBgScraper
from ingestion.scrapers.factory import ScraperFactory
from ingestion.scrapers.ndk import NdkScraper
from ingestion.scrapers.sofia_opera import SofiaOperaScraper
from ingestion.scrapers.ticketmaster import TicketmasterScraper
from ingestion.scrapers.visitsofia import VisitSofiaScraper

pytestmark = pytest.mark.unit

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _make(cls: type) -> object:
    # _parse never touches the client/semaphore, so None is fine for offline parsing.
    return cls(None, None)  # type: ignore[arg-type]


def test_factory_raises_for_unknown_source() -> None:
    with pytest.raises(ScrapingError):
        ScraperFactory.create("does-not-exist", None, None)  # type: ignore[arg-type]


def test_factory_creates_registered_source() -> None:
    scraper = ScraperFactory.create("devbg", None, None)  # type: ignore[arg-type]
    assert isinstance(scraper, DevBgScraper)
    assert "ndk" in ScraperFactory.available()


def test_devbg_parser_extracts_fields() -> None:
    html = (_FIXTURES / "devbg_list.html").read_text(encoding="utf-8")
    events = DevBgScraper._parse(_make(DevBgScraper), html)  # type: ignore[arg-type]
    assert len(events) > 0
    first = events[0]
    assert first.source == "devbg"
    assert first.title and first.start_raw
    assert first.url.startswith("https://dev.bg/")


def test_ndk_parser_extracts_fields() -> None:
    html = (_FIXTURES / "ndk_list.html").read_text(encoding="utf-8")
    events = NdkScraper._parse(_make(NdkScraper), html)  # type: ignore[arg-type]
    assert len(events) == 17
    assert all(e.external_id and e.start_raw and e.title for e in events)
    assert all("eventinfo.php?event=" in e.url for e in events)


def test_ticketmaster_parser_maps_api_response_to_raw_event() -> None:
    data = json.loads((_FIXTURES / "ticketmaster_events.json").read_text(encoding="utf-8"))
    events = TicketmasterScraper._parse(_make(TicketmasterScraper), data)  # type: ignore[arg-type]
    assert len(events) > 0
    first = events[0]
    assert first.source == "ticketmaster"
    assert first.external_id and first.start_raw and first.title


def test_sofia_opera_parser_extracts_fields() -> None:
    html = (_FIXTURES / "sofia_opera_calendar.html").read_text(encoding="utf-8")
    events = SofiaOperaScraper._parse(_make(SofiaOperaScraper), html, "2026-05")  # type: ignore[arg-type]
    assert len(events) > 0
    first = events[0]
    assert first.source == "sofia_opera"
    assert first.start_raw.startswith("2026-05") and first.title and first.url


def test_visitsofia_parser_extracts_fields() -> None:
    html = (_FIXTURES / "visitsofia_calendar.html").read_text(encoding="utf-8")
    events = VisitSofiaScraper._parse(_make(VisitSofiaScraper), html)  # type: ignore[arg-type]
    assert len(events) > 0
    first = events[0]
    assert first.source == "visitsofia"
    assert first.external_id and first.start_raw
    # de-duped by (id, date)
    assert len({e.external_id for e in events}) == len(events)
