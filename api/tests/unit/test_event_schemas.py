from __future__ import annotations

import math

import pytest

from api.schemas.events import EventPage


@pytest.mark.unit
def test_event_page_pages_exact_division() -> None:
    page = EventPage(items=[], total=40, page=1, size=20, pages=math.ceil(40 / 20))
    assert page.pages == 2


@pytest.mark.unit
def test_event_page_pages_rounds_up() -> None:
    page = EventPage(items=[], total=50, page=3, size=20, pages=math.ceil(50 / 20))
    assert page.pages == 3


@pytest.mark.unit
def test_event_page_single_page() -> None:
    page = EventPage(items=[], total=5, page=1, size=20, pages=math.ceil(5 / 20))
    assert page.pages == 1


@pytest.mark.unit
def test_event_page_zero_total() -> None:
    page = EventPage(items=[], total=0, page=1, size=20, pages=0)
    assert page.total == 0
    assert page.pages == 0
