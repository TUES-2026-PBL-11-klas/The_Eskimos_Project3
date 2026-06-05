"""The Prometheus /metrics endpoint must always be scrapeable (no DB, no auth).

We reuse the module-level ``app`` instead of calling ``create_app()`` again so the
default Prometheus registry is instrumented exactly once per process.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.unit


def test_metrics_endpoint_returns_prometheus_text() -> None:
    with TestClient(app) as client:
        resp = client.get("/metrics")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    # Always present in the default client registry, regardless of traffic.
    assert "python_gc_objects_collected_total" in resp.text
