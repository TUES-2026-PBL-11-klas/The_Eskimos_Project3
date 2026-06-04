"""Integration tests for EventRepository against the fixture database."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.repository.events import EventFilters, EventRepository


@pytest.mark.integration
async def test_get_existing_event(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    event = await repo.get(1)
    assert event is not None
    assert event.source is not None
    assert event.title


@pytest.mark.integration
async def test_get_nonexistent_event(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    assert await repo.get(999_999) is None


@pytest.mark.integration
async def test_list_returns_all_events(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(size=100))
    assert total == 50
    assert len(events) == 50


@pytest.mark.integration
async def test_list_default_pagination(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters())
    assert total == 50
    assert len(events) == 20


@pytest.mark.integration
async def test_list_page_2(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(page=2, size=20))
    assert total == 50
    assert len(events) == 20


@pytest.mark.integration
async def test_list_last_page(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(page=3, size=20))
    assert total == 50
    assert len(events) == 10


@pytest.mark.integration
async def test_list_filter_by_category(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(category_slug="music", size=50))
    assert total > 0
    for event in events:
        assert event.category is not None
        assert event.category.slug == "music"


@pytest.mark.integration
async def test_list_filter_by_city(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(city="Sofia", size=100))
    assert total == 50  # all fixture events are in Sofia
    for event in events:
        assert event.venue is not None
        assert event.venue.city == "Sofia"


@pytest.mark.integration
async def test_list_filter_by_query(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, total = await repo.list_events(EventFilters(q="Jazz", size=50))
    assert total > 0
    for event in events:
        assert "jazz" in event.title.lower()


@pytest.mark.integration
async def test_list_sorted_by_start_at(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events, _ = await repo.list_events(EventFilters(size=50))
    for i in range(1, len(events)):
        assert events[i].start_at >= events[i - 1].start_at


@pytest.mark.integration
async def test_upcoming_ordered_ascending(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events = await repo.upcoming(limit=50)
    assert len(events) > 0
    for i in range(1, len(events)):
        assert events[i].start_at >= events[i - 1].start_at


@pytest.mark.integration
async def test_upcoming_respects_limit(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events = await repo.upcoming(limit=5)
    assert len(events) <= 5


@pytest.mark.integration
async def test_upcoming_group_by_category_one_per_category(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    events = await repo.upcoming(group_by_category=True)
    category_ids = [e.category_id for e in events if e.category_id is not None]
    assert len(category_ids) == len(set(category_ids))


@pytest.mark.integration
async def test_categories_with_counts_all_seven(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    results = await repo.categories_with_counts()
    assert len(results) == 7
    names = {cat.name for cat, _ in results}
    assert names == {"Music", "Sport", "Literature", "Education", "Cinema", "Theatre", "Art"}


@pytest.mark.integration
async def test_categories_with_counts_positive(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    results = await repo.categories_with_counts()
    for _, count in results:
        assert count > 0


@pytest.mark.integration
async def test_venues_returns_all(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    venues = await repo.venues()
    assert len(venues) == 5


@pytest.mark.integration
async def test_venues_sorted_by_name(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    venues = await repo.venues()
    names = [v.name for v in venues]
    assert names == sorted(names)


@pytest.mark.integration
async def test_search_finds_matching_title(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    results = await repo.search("Jazz")
    assert len(results) > 0
    assert all("Jazz" in e.title for e in results)


@pytest.mark.integration
async def test_search_no_match_returns_empty(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    results = await repo.search("XYZNOTFOUND")
    assert results == []


@pytest.mark.integration
async def test_stats_totals(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    stats = await repo.stats()
    assert stats.total_events == 50
    assert stats.total_categories == 7
    assert stats.total_venues == 5
    assert stats.total_sources == 2
