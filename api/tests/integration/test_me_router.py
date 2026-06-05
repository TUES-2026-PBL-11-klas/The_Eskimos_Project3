"""Integration tests for /me endpoints — Phase 7 & 8: saved events, calendar, reminders.

Two throwaway containers:
  - events DB: seeded via ``events_fixture.sql`` (session-scoped, from conftest.py)
  - users DB: Alembic-migrated fresh postgres (session-scoped, defined here)

Event IDs from the fixture are serial (1-50) in insertion order. Key events used:
  - id=1  (fix-1):  Music Event #1, 2026-06-10 19:00 UTC
  - id=5  (fix-5):  Jazz Night,     2026-07-01 21:00 UTC
  - id=6  (fix-6):  Sport Event #1, 2026-06-10 18:00 UTC
  - id=47 (fix-47): Summer Music Fest, 2026-08-01 17:00 UTC  (used for reminders)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Alembic helper (copy to keep files independent of test_auth_router.py)
# ---------------------------------------------------------------------------


def _run_alembic(command: str, url: str) -> None:
    from alembic import command as alembic_cmd
    from alembic.config import Config

    import api.config as config_module

    original = config_module.settings.users_db_url
    config_module.settings.users_db_url = url  # type: ignore[misc]
    try:
        cfg = Config("alembic.ini")
        if command == "upgrade":
            alembic_cmd.upgrade(cfg, "head")
        elif command == "downgrade":
            alembic_cmd.downgrade(cfg, "base")
    finally:
        config_module.settings.users_db_url = original  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Session-scoped users container + migrated URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def me_users_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16", driver="asyncpg") as c:
        yield c


@pytest.fixture(scope="session")
def me_users_db_url(me_users_container: PostgresContainer) -> str:
    url = me_users_container.get_connection_url()
    _run_alembic("upgrade", url)
    return url


# ---------------------------------------------------------------------------
# Per-test truncation (users side only — events DB is read-only)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _truncate(me_users_db_url: str) -> AsyncIterator[None]:
    yield
    engine = create_async_engine(me_users_db_url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
    await engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client — overrides both DB sessions
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def me_client(seeded_events_db_url: str, me_users_db_url: str) -> AsyncIterator[AsyncClient]:
    from api.deps import _get_events_session, _get_users_session
    from api.main import create_app

    events_engine = create_async_engine(seeded_events_db_url)
    events_factory = async_sessionmaker(events_engine, expire_on_commit=False)

    users_engine = create_async_engine(me_users_db_url)
    users_factory = async_sessionmaker(users_engine, expire_on_commit=False)

    async def _events_override() -> AsyncIterator[AsyncSession]:
        async with events_factory() as session:
            yield session

    async def _users_override() -> AsyncIterator[AsyncSession]:
        async with users_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[_get_events_session] = _events_override
    app.dependency_overrides[_get_users_session] = _users_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    await events_engine.dispose()
    await users_engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(
    client: AsyncClient, email: str = "u@test.com", pw: str = "pass123"
) -> dict[str, Any]:
    r = await client.post("/auth/register", json={"email": email, "password": pw})
    assert r.status_code == 201
    return r.json()  # type: ignore[no-any-return]


async def _login(client: AsyncClient, email: str = "u@test.com", pw: str = "pass123") -> str:
    r = await client.post("/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200
    return str(r.json()["token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _save(client: AsyncClient, token: str, event_id: int) -> dict[str, Any]:
    r = await client.post(f"/me/saved/{event_id}", headers=_auth(token))
    assert r.status_code == 201
    return r.json()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Auth enforcement
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_save_requires_auth(me_client: AsyncClient) -> None:
    r = await me_client.post("/me/saved/1")
    assert r.status_code == 401


@pytest.mark.integration
async def test_list_requires_auth(me_client: AsyncClient) -> None:
    r = await me_client.get("/me/saved")
    assert r.status_code == 401


@pytest.mark.integration
async def test_calendar_requires_auth(me_client: AsyncClient) -> None:
    r = await me_client.get("/me/calendar")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /me/saved/{event_id}
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_save_event_creates_snapshot(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    data = await _save(me_client, token, 1)

    assert data["title"] == "Music Event #1"
    assert data["source"] == "fixture_scraper"
    assert data["external_id"] == "fix-1"
    assert data["event_id"] == 1  # originating events-DB id, for the save toggle
    assert data["venue_name"] == "National Palace of Culture"
    assert data["city"] == "Sofia"
    assert data["category"] == "Music"
    assert "id" in data
    assert "saved_at" in data
    assert "password_hash" not in data


@pytest.mark.integration
async def test_save_event_not_found_returns_404(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    r = await me_client.post("/me/saved/9999", headers=_auth(token))
    assert r.status_code == 404


@pytest.mark.integration
async def test_save_event_duplicate_returns_409(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    await _save(me_client, token, 1)
    r = await me_client.post("/me/saved/1", headers=_auth(token))
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# GET /me/saved
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_list_saved_empty_for_new_user(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    r = await me_client.get("/me/saved", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.integration
async def test_list_saved_ordered_by_start_at(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    # event 1: 2026-06-10 19:00 UTC; event 6: 2026-06-10 18:00 UTC (earlier)
    await _save(me_client, token, 1)
    await _save(me_client, token, 6)
    r = await me_client.get("/me/saved", headers=_auth(token))
    items: list[dict[str, Any]] = r.json()
    assert len(items) == 2
    assert items[0]["external_id"] == "fix-6"  # 18:00 sorts before 19:00
    assert items[1]["external_id"] == "fix-1"


# ---------------------------------------------------------------------------
# DELETE /me/saved/{saved_id}
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_unsave_event_returns_204(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 1)
    r = await me_client.delete(f"/me/saved/{saved['id']}", headers=_auth(token))
    assert r.status_code == 204
    listed = await me_client.get("/me/saved", headers=_auth(token))
    assert listed.json() == []


@pytest.mark.integration
async def test_unsave_nonexistent_returns_404(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    r = await me_client.delete("/me/saved/9999", headers=_auth(token))
    assert r.status_code == 404


@pytest.mark.integration
async def test_unsave_other_users_saved_returns_404(me_client: AsyncClient) -> None:
    await _register(me_client, "a@a.com", "pass")
    await _register(me_client, "b@b.com", "pass")
    token_a = await _login(me_client, "a@a.com", "pass")
    token_b = await _login(me_client, "b@b.com", "pass")
    saved_by_a = await _save(me_client, token_a, 1)
    r = await me_client.delete(f"/me/saved/{saved_by_a['id']}", headers=_auth(token_b))
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /me/calendar
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_calendar_month_filter(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    await _save(me_client, token, 1)  # 2026-06-10
    await _save(me_client, token, 5)  # 2026-07-01
    r = await me_client.get("/me/calendar?month=2026-06", headers=_auth(token))
    assert r.status_code == 200
    days: list[dict[str, Any]] = r.json()["days"]
    assert len(days) == 1
    assert days[0]["date"] == "2026-06-10"
    assert len(days[0]["events"]) == 1
    assert days[0]["events"][0]["external_id"] == "fix-1"


@pytest.mark.integration
async def test_calendar_from_to_filter(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    await _save(me_client, token, 1)  # 2026-06-10
    await _save(me_client, token, 5)  # 2026-07-01
    r = await me_client.get("/me/calendar?from=2026-07-01&to=2026-07-31", headers=_auth(token))
    assert r.status_code == 200
    days = r.json()["days"]
    assert len(days) == 1
    assert days[0]["date"] == "2026-07-01"
    assert days[0]["events"][0]["external_id"] == "fix-5"


@pytest.mark.integration
async def test_calendar_groups_same_day_events(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    # events 1 and 6 both fall on 2026-06-10 UTC
    await _save(me_client, token, 1)  # 19:00 UTC
    await _save(me_client, token, 6)  # 18:00 UTC
    r = await me_client.get("/me/calendar?month=2026-06", headers=_auth(token))
    days = r.json()["days"]
    assert len(days) == 1
    assert days[0]["date"] == "2026-06-10"
    assert len(days[0]["events"]) == 2


@pytest.mark.integration
async def test_calendar_empty_when_no_saved_events(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    r = await me_client.get("/me/calendar?month=2026-06", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["days"] == []


# ---------------------------------------------------------------------------
# POST /me/saved/{saved_id}/reminder
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_create_reminder_with_lead_hours_returns_201(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)  # 2026-08-01 17:00 UTC
    r = await me_client.post(
        f"/me/saved/{saved['id']}/reminder",
        json={"lead_hours": 100},  # remind_at ≈ 2026-07-27 21:00 UTC (future)
        headers=_auth(token),
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert data["saved_event_id"] == saved["id"]
    assert "remind_at" in data
    assert "id" in data


@pytest.mark.integration
async def test_create_reminder_with_explicit_remind_at(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)
    future_dt = "2026-07-20T12:00:00Z"
    r = await me_client.post(
        f"/me/saved/{saved['id']}/reminder",
        json={"remind_at": future_dt},
        headers=_auth(token),
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


@pytest.mark.integration
async def test_create_reminder_uses_default_lead_hours(me_client: AsyncClient) -> None:
    # User default is 24h; event 47 is 2026-08-01 17:00 UTC → remind_at = 2026-07-31 17:00 UTC
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)
    r = await me_client.post(
        f"/me/saved/{saved['id']}/reminder",
        json={},  # no lead_hours or remind_at — uses preference default
        headers=_auth(token),
    )
    assert r.status_code == 201


@pytest.mark.integration
async def test_create_reminder_past_remind_at_returns_422(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)  # 2026-08-01 17:00 UTC
    # lead_hours=2000 → remind_at ≈ 2026-05-10 — well in the past
    r = await me_client.post(
        f"/me/saved/{saved['id']}/reminder",
        json={"lead_hours": 2000},
        headers=_auth(token),
    )
    assert r.status_code == 422


@pytest.mark.integration
async def test_create_reminder_for_nonexistent_saved_event_returns_404(
    me_client: AsyncClient,
) -> None:
    await _register(me_client)
    token = await _login(me_client)
    r = await me_client.post(
        "/me/saved/9999/reminder",
        json={"lead_hours": 100},
        headers=_auth(token),
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /me/reminders  &  DELETE /me/reminders/{id}
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_list_reminders_returns_all_for_user(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)
    await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 100}, headers=_auth(token)
    )
    await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 200}, headers=_auth(token)
    )
    r = await me_client.get("/me/reminders", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.integration
async def test_cancel_reminder_sets_status_cancelled(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)
    cr = await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 100}, headers=_auth(token)
    )
    reminder_id = cr.json()["id"]
    r = await me_client.delete(f"/me/reminders/{reminder_id}", headers=_auth(token))
    assert r.status_code == 204
    listed = await me_client.get("/me/reminders", headers=_auth(token))
    assert listed.json()[0]["status"] == "cancelled"


@pytest.mark.integration
async def test_cancel_other_users_reminder_returns_404(me_client: AsyncClient) -> None:
    await _register(me_client, "a@a.com", "pass")
    await _register(me_client, "b@b.com", "pass")
    token_a = await _login(me_client, "a@a.com", "pass")
    token_b = await _login(me_client, "b@b.com", "pass")
    saved = await _save(me_client, token_a, 47)
    cr = await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 100}, headers=_auth(token_a)
    )
    r = await me_client.delete(f"/me/reminders/{cr.json()['id']}", headers=_auth(token_b))
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /me/reminders/due
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_due_reminders_empty_when_remind_at_in_future(me_client: AsyncClient) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)
    await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 100}, headers=_auth(token)
    )
    r = await me_client.get("/me/reminders/due", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.integration
async def test_due_reminders_returns_when_remind_at_in_past(
    me_client: AsyncClient, me_users_db_url: str
) -> None:
    await _register(me_client)
    token = await _login(me_client)
    saved = await _save(me_client, token, 47)  # event start: 2026-08-01 (future)
    cr = await me_client.post(
        f"/me/saved/{saved['id']}/reminder", json={"lead_hours": 100}, headers=_auth(token)
    )
    reminder_id = cr.json()["id"]

    # Backdate remind_at so it appears "due"
    engine = create_async_engine(me_users_db_url)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE reminders SET remind_at = :past WHERE id = :id"),
            {"past": datetime(2000, 1, 1, tzinfo=UTC), "id": reminder_id},
        )
    await engine.dispose()

    r = await me_client.get("/me/reminders/due", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == reminder_id


@pytest.mark.integration
async def test_reminders_requires_auth(me_client: AsyncClient) -> None:
    r = await me_client.get("/me/reminders")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /me  &  PATCH /me  (profile + preferences)
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_get_me_requires_auth(me_client: AsyncClient) -> None:
    r = await me_client.get("/me")
    assert r.status_code == 401


@pytest.mark.integration
async def test_get_me_returns_profile_and_default_preferences(me_client: AsyncClient) -> None:
    await _register(me_client, "p@test.com", "pass123")
    token = await _login(me_client, "p@test.com", "pass123")
    r = await me_client.get("/me", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "p@test.com"
    assert "password_hash" not in data
    # Preferences row is created at register-time with the documented defaults.
    assert data["preferences"]["default_lead_hours"] == 24
    assert data["preferences"]["timezone"] == "Europe/Sofia"


@pytest.mark.integration
async def test_patch_me_updates_profile_and_preferences(me_client: AsyncClient) -> None:
    await _register(me_client, "p@test.com", "pass123")
    token = await _login(me_client, "p@test.com", "pass123")
    r = await me_client.patch(
        "/me",
        json={"display_name": "Pepi", "default_lead_hours": 48, "timezone": "UTC"},
        headers=_auth(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["display_name"] == "Pepi"
    assert data["preferences"]["default_lead_hours"] == 48
    assert data["preferences"]["timezone"] == "UTC"
    # Persisted across requests.
    again = await me_client.get("/me", headers=_auth(token))
    assert again.json()["preferences"]["default_lead_hours"] == 48


@pytest.mark.integration
async def test_patch_me_partial_update_leaves_other_fields(me_client: AsyncClient) -> None:
    await _register(me_client, "p@test.com", "pass123")
    token = await _login(me_client, "p@test.com", "pass123")
    await me_client.patch("/me", json={"default_lead_hours": 12}, headers=_auth(token))
    r = await me_client.patch("/me", json={"display_name": "Solo"}, headers=_auth(token))
    data = r.json()
    assert data["display_name"] == "Solo"
    assert data["preferences"]["default_lead_hours"] == 12  # untouched by second patch
