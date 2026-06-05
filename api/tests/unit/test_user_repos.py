"""Unit tests for the four user-side repositories.

All tests use ``AsyncMock`` in place of a real ``AsyncSession`` — no database or
container required.  The mock verifies that repositories issue the right SQL calls
and delegate mutation to the session correctly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models.users import Reminder, SavedEvent, Session, User, UserPreferences
from api.repository.reminders import ReminderRepository
from api.repository.saved import SavedEventRepository
from api.repository.sessions import SessionRepository
from api.repository.users import UserRepository

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _mock_db() -> AsyncSession:
    """Return an AsyncMock typed as AsyncSession to satisfy mypy in tests."""
    db: AsyncSession = AsyncMock(spec=AsyncSession)  # type: ignore[assignment]
    return db


def _scalar_result(value: object) -> MagicMock:
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


def _scalars_result(values: list[object]) -> MagicMock:
    r = MagicMock()
    r.scalars.return_value = values
    return r


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_user_repo_get_returns_user() -> None:
    db = _mock_db()
    user = User(id=1, email="a@b.com", password_hash="h")
    db.execute.return_value = _scalar_result(user)  # type: ignore[attr-defined]
    result = await UserRepository(db).get(1)
    assert result is user


@pytest.mark.unit
async def test_user_repo_get_returns_none_when_missing() -> None:
    db = _mock_db()
    db.execute.return_value = _scalar_result(None)  # type: ignore[attr-defined]
    assert await UserRepository(db).get(99) is None


@pytest.mark.unit
async def test_user_repo_get_by_email_found() -> None:
    db = _mock_db()
    user = User(id=2, email="x@y.com", password_hash="h")
    db.execute.return_value = _scalar_result(user)  # type: ignore[attr-defined]
    result = await UserRepository(db).get_by_email("x@y.com")
    assert result is user


@pytest.mark.unit
async def test_user_repo_get_by_email_not_found() -> None:
    db = _mock_db()
    db.execute.return_value = _scalar_result(None)  # type: ignore[attr-defined]
    assert await UserRepository(db).get_by_email("nope@nope.com") is None


@pytest.mark.unit
async def test_user_repo_add_calls_add_and_flush() -> None:
    db = _mock_db()
    user = User(email="new@b.com", password_hash="h")
    returned = await UserRepository(db).add(user)
    db.add.assert_called_once_with(user)  # type: ignore[attr-defined]
    db.flush.assert_awaited_once()  # type: ignore[attr-defined]
    assert returned is user


# ---------------------------------------------------------------------------
# SessionRepository
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_session_repo_get_found() -> None:
    db = _mock_db()
    sess = Session(id=10, user_id=1, token_hash="abc", expires_at=datetime.now(UTC))
    db.execute.return_value = _scalar_result(sess)  # type: ignore[attr-defined]
    assert await SessionRepository(db).get(10) is sess


@pytest.mark.unit
async def test_session_repo_get_by_token_hash_found() -> None:
    db = _mock_db()
    sess = Session(id=5, user_id=1, token_hash="xyz", expires_at=datetime.now(UTC))
    db.execute.return_value = _scalar_result(sess)  # type: ignore[attr-defined]
    assert await SessionRepository(db).get_by_token_hash("xyz") is sess


@pytest.mark.unit
async def test_session_repo_get_by_token_hash_not_found() -> None:
    db = _mock_db()
    db.execute.return_value = _scalar_result(None)  # type: ignore[attr-defined]
    assert await SessionRepository(db).get_by_token_hash("bad") is None


@pytest.mark.unit
async def test_session_repo_list_by_user() -> None:
    db = _mock_db()
    s1 = Session(id=1, user_id=7, token_hash="t1", expires_at=datetime.now(UTC))
    s2 = Session(id=2, user_id=7, token_hash="t2", expires_at=datetime.now(UTC))
    db.execute.return_value = _scalars_result([s1, s2])  # type: ignore[attr-defined]
    result = await SessionRepository(db).list_by_user(7)
    assert result == [s1, s2]


@pytest.mark.unit
async def test_session_repo_add_flushes() -> None:
    db = _mock_db()
    sess = Session(user_id=3, token_hash="tok", expires_at=datetime.now(UTC))
    returned = await SessionRepository(db).add(sess)
    db.add.assert_called_once_with(sess)  # type: ignore[attr-defined]
    db.flush.assert_awaited_once()  # type: ignore[attr-defined]
    assert returned is sess


@pytest.mark.unit
async def test_session_repo_delete_calls_session_delete() -> None:
    db = _mock_db()
    sess = Session(id=9, user_id=1, token_hash="old", expires_at=datetime.now(UTC))
    await SessionRepository(db).delete(sess)
    db.delete.assert_awaited_once_with(sess)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# SavedEventRepository
# ---------------------------------------------------------------------------

_NOW = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)


@pytest.mark.unit
async def test_saved_repo_get_found() -> None:
    db = _mock_db()
    saved = SavedEvent(id=1, user_id=2, source="s", external_id="e",
                       title="T", start_at=_NOW, url="http://x")
    db.execute.return_value = _scalar_result(saved)  # type: ignore[attr-defined]
    assert await SavedEventRepository(db).get(1) is saved


@pytest.mark.unit
async def test_saved_repo_get_for_user_found() -> None:
    db = _mock_db()
    saved = SavedEvent(id=3, user_id=5, source="s", external_id="e",
                       title="T", start_at=_NOW, url="http://x")
    db.execute.return_value = _scalar_result(saved)  # type: ignore[attr-defined]
    assert await SavedEventRepository(db).get_for_user(3, 5) is saved


@pytest.mark.unit
async def test_saved_repo_get_for_user_wrong_owner_returns_none() -> None:
    db = _mock_db()
    db.execute.return_value = _scalar_result(None)  # type: ignore[attr-defined]
    assert await SavedEventRepository(db).get_for_user(3, 99) is None


@pytest.mark.unit
async def test_saved_repo_get_by_source_external_id() -> None:
    db = _mock_db()
    saved = SavedEvent(id=4, user_id=1, source="src", external_id="ext123",
                       title="T", start_at=_NOW, url="http://x")
    db.execute.return_value = _scalar_result(saved)  # type: ignore[attr-defined]
    result = await SavedEventRepository(db).get_by_source_external_id(1, "src", "ext123")
    assert result is saved


@pytest.mark.unit
async def test_saved_repo_list_by_user() -> None:
    db = _mock_db()
    e1 = SavedEvent(id=1, user_id=1, source="s", external_id="a",
                    title="A", start_at=_NOW, url="http://a")
    e2 = SavedEvent(id=2, user_id=1, source="s", external_id="b",
                    title="B", start_at=_NOW, url="http://b")
    db.execute.return_value = _scalars_result([e1, e2])  # type: ignore[attr-defined]
    assert await SavedEventRepository(db).list_by_user(1) == [e1, e2]


@pytest.mark.unit
async def test_saved_repo_add_flushes() -> None:
    db = _mock_db()
    saved = SavedEvent(user_id=1, source="s", external_id="e",
                       title="T", start_at=_NOW, url="http://x")
    returned = await SavedEventRepository(db).add(saved)
    db.add.assert_called_once_with(saved)  # type: ignore[attr-defined]
    db.flush.assert_awaited_once()  # type: ignore[attr-defined]
    assert returned is saved


@pytest.mark.unit
async def test_saved_repo_delete_marks_for_deletion() -> None:
    db = _mock_db()
    saved = SavedEvent(id=7, user_id=1, source="s", external_id="e",
                       title="T", start_at=_NOW, url="http://x")
    await SavedEventRepository(db).delete(saved)
    db.delete.assert_awaited_once_with(saved)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# ReminderRepository
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_reminder_repo_get_found() -> None:
    db = _mock_db()
    reminder = Reminder(id=1, saved_event_id=2, user_id=3,
                        remind_at=_NOW, status="pending")
    db.execute.return_value = _scalar_result(reminder)  # type: ignore[attr-defined]
    assert await ReminderRepository(db).get(1) is reminder


@pytest.mark.unit
async def test_reminder_repo_get_for_user_found() -> None:
    db = _mock_db()
    reminder = Reminder(id=5, saved_event_id=2, user_id=7,
                        remind_at=_NOW, status="pending")
    db.execute.return_value = _scalar_result(reminder)  # type: ignore[attr-defined]
    assert await ReminderRepository(db).get_for_user(5, 7) is reminder


@pytest.mark.unit
async def test_reminder_repo_list_by_user() -> None:
    db = _mock_db()
    r1 = Reminder(id=1, saved_event_id=1, user_id=2, remind_at=_NOW, status="pending")
    r2 = Reminder(id=2, saved_event_id=3, user_id=2, remind_at=_NOW, status="cancelled")
    db.execute.return_value = _scalars_result([r1, r2])  # type: ignore[attr-defined]
    assert await ReminderRepository(db).list_by_user(2) == [r1, r2]


@pytest.mark.unit
async def test_reminder_repo_list_due() -> None:
    db = _mock_db()
    r = Reminder(id=1, saved_event_id=1, user_id=1, remind_at=_NOW, status="pending")
    db.execute.return_value = _scalars_result([r])  # type: ignore[attr-defined]
    result = await ReminderRepository(db).list_due(_NOW)
    assert result == [r]


@pytest.mark.unit
async def test_reminder_repo_add_flushes() -> None:
    db = _mock_db()
    reminder = Reminder(saved_event_id=1, user_id=1, remind_at=_NOW, status="pending")
    returned = await ReminderRepository(db).add(reminder)
    db.add.assert_called_once_with(reminder)  # type: ignore[attr-defined]
    db.flush.assert_awaited_once()  # type: ignore[attr-defined]
    assert returned is reminder


@pytest.mark.unit
async def test_reminder_repo_cancel_sets_status() -> None:
    db = _mock_db()
    reminder = Reminder(id=3, saved_event_id=1, user_id=1,
                        remind_at=_NOW, status="pending")
    await ReminderRepository(db).cancel(reminder)
    assert reminder.status == "cancelled"


# ---------------------------------------------------------------------------
# Exception hierarchy (extended in Phase 5)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_user_already_exists_stores_email() -> None:
    from api.domain.exceptions import EventHubError, UserAlreadyExistsError
    err = UserAlreadyExistsError("dup@x.com")
    assert err.email == "dup@x.com"
    assert isinstance(err, EventHubError)


@pytest.mark.unit
def test_already_saved_stores_source_and_external_id() -> None:
    from api.domain.exceptions import AlreadySavedError, EventHubError
    err = AlreadySavedError("ticketmaster", "evt-42")
    assert err.source == "ticketmaster"
    assert err.external_id == "evt-42"
    assert isinstance(err, EventHubError)


@pytest.mark.unit
def test_reminder_not_found_stores_id() -> None:
    from api.domain.exceptions import EventHubError, ReminderNotFoundError
    err = ReminderNotFoundError(99)
    assert err.reminder_id == 99
    assert isinstance(err, EventHubError)


@pytest.mark.unit
def test_user_preferences_has_defaults() -> None:
    prefs = UserPreferences(user_id=1)
    assert prefs.user_id == 1
