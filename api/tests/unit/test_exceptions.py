from __future__ import annotations

import pytest

from api.domain.exceptions import EventHubError, EventNotFoundError


@pytest.mark.unit
def test_event_not_found_is_event_hub_error() -> None:
    assert isinstance(EventNotFoundError(1), EventHubError)


@pytest.mark.unit
def test_event_not_found_stores_id() -> None:
    err = EventNotFoundError(42)
    assert err.event_id == 42


@pytest.mark.unit
def test_event_not_found_message_contains_id() -> None:
    assert "99" in str(EventNotFoundError(99))
