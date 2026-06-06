"""Unit tests for the pipeline steps (offline — no DB, no network)."""

from __future__ import annotations

from typing import Any

import pytest

from ingestion.domain.categories import Category
from ingestion.domain.models import NormalizedEvent, RawEvent
from ingestion.exceptions import InvalidEventDataError
from ingestion.pipeline.categorizer import Categorizer
from ingestion.pipeline.deduplicator import Deduplicator
from ingestion.pipeline.normalizer import Normalizer
from ingestion.pipeline.past_event_filter import PastEventFilter
from ingestion.pipeline.validator import Validator

pytestmark = pytest.mark.unit


def _raw(**overrides: Any) -> RawEvent:
    base: dict[str, Any] = {
        "source": "t",
        "external_id": "1",
        "title": "Title",
        "start_raw": "2030-06-01 20:00",
        "url": "http://x",
    }
    base.update(overrides)
    return RawEvent(**base)


async def test_normalizer_strips_html_from_description() -> None:
    ne = await Normalizer().process(_raw(description="<p>Hello <b>world</b></p>"))
    assert isinstance(ne, NormalizedEvent)
    assert ne.description == "Hello world"


async def test_normalizer_parses_sofia_local_time_to_utc() -> None:
    ne = await Normalizer().process(_raw(start_raw="2030-06-01 20:00"))
    assert isinstance(ne, NormalizedEvent)
    assert ne.start_at.utcoffset() is not None
    assert ne.start_at.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
    # 20:00 Sofia (EEST, UTC+3 in June) -> 17:00 UTC
    assert (ne.start_at.hour, ne.start_at.month) == (17, 6)


async def test_validator_drops_event_missing_required_field() -> None:
    with pytest.raises(InvalidEventDataError):
        await Validator().process(_raw(start_raw=None))


async def test_categorizer_falls_back_to_uncategorized() -> None:
    ne = await Normalizer().process(_raw(title="Neighbourhood get-together"))
    out = await Categorizer().process(ne)
    assert isinstance(out, NormalizedEvent)
    assert out.category == Category.UNCATEGORIZED


async def test_categorizer_detects_music_keyword() -> None:
    ne = await Normalizer().process(_raw(title="Jazz concert downtown"))
    out = await Categorizer().process(ne)
    assert isinstance(out, NormalizedEvent)
    assert out.category == Category.MUSIC


async def test_past_event_filter_drops_old_event() -> None:
    ne = await Normalizer().process(_raw(start_raw="2020-01-01 20:00"))
    assert isinstance(ne, NormalizedEvent)
    result = await PastEventFilter().process(ne)
    assert result is None


async def test_past_event_filter_keeps_future_event() -> None:
    ne = await Normalizer().process(_raw(start_raw="2030-06-01 20:00"))
    assert isinstance(ne, NormalizedEvent)
    result = await PastEventFilter().process(ne)
    assert result is ne


async def test_past_event_filter_passes_raw_event_through() -> None:
    raw = _raw()
    result = await PastEventFilter().process(raw)
    assert result is raw


class _FakeRepo:
    async def find_duplicate(self, event: NormalizedEvent) -> NormalizedEvent | None:
        return None


async def test_deduplicator_identifies_same_event_different_source() -> None:
    dedup = Deduplicator(_FakeRepo())  # type: ignore[arg-type]
    n1 = await Normalizer().process(
        _raw(source="A", title="Same Show", venue_city="Sofia", description=None)
    )
    n2 = await Normalizer().process(
        _raw(source="B", title="Same Show", venue_city="Sofia", description="Full lineup")
    )
    r1 = await dedup.process(n1)
    r2 = await dedup.process(n2)
    assert r1 is n1
    assert r2 is None  # second dropped as duplicate
    assert isinstance(n1, NormalizedEvent)
    assert n1.description == "Full lineup"  # missing field merged in from the duplicate
