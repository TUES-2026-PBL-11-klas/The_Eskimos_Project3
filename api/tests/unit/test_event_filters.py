from __future__ import annotations

import pytest

from api.repository.events import EventFilters


@pytest.mark.unit
def test_defaults() -> None:
    f = EventFilters()
    assert f.page == 1
    assert f.size == 20
    assert f.q is None
    assert f.category_slug is None
    assert f.city is None
    assert f.date_from is None
    assert f.date_to is None


@pytest.mark.unit
def test_custom_pagination() -> None:
    f = EventFilters(page=3, size=10)
    assert f.page == 3
    assert f.size == 10
