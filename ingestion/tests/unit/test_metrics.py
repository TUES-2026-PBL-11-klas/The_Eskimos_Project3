"""Run metrics push to the Prometheus Pushgateway.

Offline by design: we snapshot the registry directly and monkeypatch the gateway call,
so no network or running Pushgateway is needed.
"""

from __future__ import annotations

import pytest

import ingestion.metrics as metrics_mod
from ingestion.metrics import Metrics

pytestmark = pytest.mark.unit


def _make_metrics() -> Metrics:
    m = Metrics()
    m.scraped("ticketmaster")
    m.scraped("ticketmaster")
    m.scraped("bandsintown")
    m.normalized()
    m.normalized()
    m.deduplicated()
    return m


def test_build_registry_has_the_four_metrics_with_labels() -> None:
    registry = _make_metrics().build_registry()

    assert registry.get_sample_value("events_scraped_total", {"source": "ticketmaster"}) == 2.0
    assert registry.get_sample_value("events_scraped_total", {"source": "bandsintown"}) == 1.0
    assert registry.get_sample_value("events_normalized_total") == 2.0
    assert registry.get_sample_value("events_deduplicated_total") == 1.0
    # Gauge is set to the elapsed wall-clock; just assert it exists and is non-negative.
    duration = registry.get_sample_value("pipeline_duration_seconds")
    assert duration is not None and duration >= 0.0


def test_push_calls_gateway_with_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_push(gateway: str, *, job: str, registry: object) -> None:
        # Confirm the populated registry is what gets pushed.
        assert registry.get_sample_value("events_normalized_total") == 2.0  # type: ignore[attr-defined]
        calls.append((gateway, job))

    monkeypatch.setattr(metrics_mod, "prom_push_to_gateway", fake_push)

    _make_metrics().push("http://pushgateway:9091")

    assert calls == [("http://pushgateway:9091", "ingestion")]


def test_push_failure_is_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise ConnectionError("gateway down")

    monkeypatch.setattr(metrics_mod, "prom_push_to_gateway", boom)

    # Must not raise — a gateway outage cannot fail the ingestion run.
    _make_metrics().push("http://pushgateway:9091")
