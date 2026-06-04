"""Integration tests for the public events router against the fixture database."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_list_events_default_pagination(client: AsyncClient) -> None:
    r = await client.get("/events")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 50
    assert len(data["items"]) == 20
    assert data["page"] == 1
    assert data["size"] == 20
    assert data["pages"] == 3


@pytest.mark.integration
async def test_list_events_page_2(client: AsyncClient) -> None:
    r = await client.get("/events?page=2&size=20")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert len(data["items"]) == 20


@pytest.mark.integration
async def test_list_events_filter_by_category(client: AsyncClient) -> None:
    r = await client.get("/events?category=music&size=50")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["category"]["slug"] == "music"


@pytest.mark.integration
async def test_list_events_filter_by_city(client: AsyncClient) -> None:
    r = await client.get("/events?city=Sofia&size=100")
    assert r.status_code == 200
    assert r.json()["total"] == 50  # all fixture events are in Sofia


@pytest.mark.integration
async def test_list_events_filter_by_q(client: AsyncClient) -> None:
    r = await client.get("/events?q=Jazz&size=50")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert "jazz" in item["title"].lower()


@pytest.mark.integration
async def test_list_events_sorted_by_start_at(client: AsyncClient) -> None:
    r = await client.get("/events?size=50")
    assert r.status_code == 200
    items = r.json()["items"]
    for i in range(1, len(items)):
        assert items[i]["start_at"] >= items[i - 1]["start_at"]


@pytest.mark.integration
async def test_get_event_returns_200(client: AsyncClient) -> None:
    r = await client.get("/events/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["title"]
    assert data["source"] is not None


@pytest.mark.integration
async def test_get_event_returns_404(client: AsyncClient) -> None:
    r = await client.get("/events/999999")
    assert r.status_code == 404


@pytest.mark.integration
async def test_upcoming_returns_ordered(client: AsyncClient) -> None:
    r = await client.get("/events/upcoming?limit=50")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    for i in range(1, len(items)):
        assert items[i]["start_at"] >= items[i - 1]["start_at"]


@pytest.mark.integration
async def test_upcoming_group_by_category_one_per_category(client: AsyncClient) -> None:
    r = await client.get("/events/upcoming?group_by=true")
    assert r.status_code == 200
    items = r.json()
    cat_ids = [it["category"]["id"] for it in items if it["category"]]
    assert len(cat_ids) == len(set(cat_ids))


@pytest.mark.integration
async def test_categories_returns_all_seven(client: AsyncClient) -> None:
    r = await client.get("/categories")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7
    names = {item["category"]["name"] for item in data}
    assert names == {"Music", "Sport", "Literature", "Education", "Cinema", "Theatre", "Art"}


@pytest.mark.integration
async def test_categories_have_positive_counts(client: AsyncClient) -> None:
    r = await client.get("/categories")
    assert r.status_code == 200
    for item in r.json():
        assert item["count"] > 0


@pytest.mark.integration
async def test_venues_returns_all_five(client: AsyncClient) -> None:
    r = await client.get("/venues")
    assert r.status_code == 200
    assert len(r.json()) == 5


@pytest.mark.integration
async def test_search_finds_matching_events(client: AsyncClient) -> None:
    r = await client.get("/search?q=Jazz")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    assert all("Jazz" in item["title"] for item in items)


@pytest.mark.integration
async def test_search_returns_empty_for_no_match(client: AsyncClient) -> None:
    r = await client.get("/search?q=XYZNOTFOUND")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.integration
async def test_stats_returns_correct_totals(client: AsyncClient) -> None:
    r = await client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 50
    assert data["total_categories"] == 7
    assert data["total_venues"] == 5
    assert data["total_sources"] == 2


@pytest.mark.integration
async def test_cache_control_header_present(client: AsyncClient) -> None:
    for path in ["/events", "/events/1", "/events/upcoming", "/categories", "/venues", "/stats"]:
        r = await client.get(path)
        assert r.status_code == 200, path
        cc = r.headers.get("cache-control", "")
        assert "max-age=" in cc, f"Cache-Control missing on {path}"
        assert "public" in cc, f"Cache-Control not public on {path}"
