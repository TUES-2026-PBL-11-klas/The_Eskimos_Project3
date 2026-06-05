"""Unit tests for AuthService.

All tests use ``unittest.mock`` — no DB or container required.
bcrypt is patched so the test suite stays fast.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.db.models.users import Session, User
from api.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from api.repository.sessions import SessionRepository
from api.repository.users import UserRepository
from api.services.auth import AuthService

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _user_repo() -> UserRepository:
    r: UserRepository = AsyncMock(spec=UserRepository)  # type: ignore[assignment]
    return r


def _session_repo() -> SessionRepository:
    r: SessionRepository = AsyncMock(spec=SessionRepository)  # type: ignore[assignment]
    return r


def _make_user(
    user_id: int = 1,
    email: str = "a@b.com",
    pw_hash: str = "hashed",
) -> User:
    return User(id=user_id, email=email, password_hash=pw_hash)


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_register_creates_user_and_prefs() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = None  # type: ignore[attr-defined]
    created_user = _make_user()
    ur.add.return_value = created_user  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.gensalt.return_value = b"salt"
        mock_bcrypt.hashpw.return_value = b"hashed"
        service = AuthService(ur, sr)
        user = await service.register("a@b.com", "password123")

    ur.get_by_email.assert_awaited_once_with("a@b.com")  # type: ignore[attr-defined]
    ur.add.assert_awaited_once()  # type: ignore[attr-defined]
    ur.add_preferences.assert_awaited_once()  # type: ignore[attr-defined]
    assert user is created_user


@pytest.mark.unit
async def test_register_raises_on_duplicate_email() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = _make_user()  # type: ignore[attr-defined]

    service = AuthService(ur, sr)
    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await service.register("a@b.com", "pass")

    assert exc_info.value.email == "a@b.com"
    ur.add.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.unit
async def test_register_raises_on_password_too_long() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = None  # type: ignore[attr-defined]

    service = AuthService(ur, sr)
    long_pw = "x" * 73
    with pytest.raises(ValueError, match="72 bytes"):
        await service.register("a@b.com", long_pw)

    ur.add.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.unit
async def test_register_accepts_password_exactly_72_bytes() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = None  # type: ignore[attr-defined]
    ur.add.return_value = _make_user()  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.gensalt.return_value = b"salt"
        mock_bcrypt.hashpw.return_value = b"hashed"
        service = AuthService(ur, sr)
        await service.register("a@b.com", "x" * 72)

    ur.add.assert_awaited_once()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_login_returns_token_and_expiry() -> None:
    ur = _user_repo()
    sr = _session_repo()
    user = _make_user(pw_hash="hashed")
    ur.get_by_email.return_value = user  # type: ignore[attr-defined]
    sr.add.return_value = MagicMock()  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.checkpw.return_value = True
        service = AuthService(ur, sr)
        token, expires_at = await service.login("a@b.com", "password")

    assert isinstance(token, str)
    assert isinstance(expires_at, datetime)
    assert expires_at > datetime.now(UTC)
    sr.add.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.unit
async def test_login_raises_on_unknown_email() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = None  # type: ignore[attr-defined]

    service = AuthService(ur, sr)
    with pytest.raises(InvalidCredentialsError):
        await service.login("no@body.com", "pass")

    sr.add.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.unit
async def test_login_raises_on_wrong_password() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = _make_user()  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.checkpw.return_value = False
        service = AuthService(ur, sr)
        with pytest.raises(InvalidCredentialsError):
            await service.login("a@b.com", "wrongpass")

    sr.add.assert_not_awaited()  # type: ignore[attr-defined]


@pytest.mark.unit
async def test_login_stores_sha256_hash_not_plain_token() -> None:
    import hashlib

    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = _make_user()  # type: ignore[attr-defined]

    captured: list[Session] = []

    async def _capture_add(s: Session) -> Session:
        captured.append(s)
        return s

    sr.add.side_effect = _capture_add  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.checkpw.return_value = True
        service = AuthService(ur, sr)
        token, _ = await service.login("a@b.com", "pass")

    assert len(captured) == 1
    expected_hash = hashlib.sha256(token.encode()).hexdigest()
    assert captured[0].token_hash == expected_hash
    assert captured[0].token_hash != token


@pytest.mark.unit
async def test_login_forwards_user_agent() -> None:
    ur = _user_repo()
    sr = _session_repo()
    ur.get_by_email.return_value = _make_user()  # type: ignore[attr-defined]
    sr.add.return_value = MagicMock()  # type: ignore[attr-defined]

    captured: list[Session] = []

    async def _capture(s: Session) -> Session:
        captured.append(s)
        return s

    sr.add.side_effect = _capture  # type: ignore[attr-defined]

    with patch("api.services.auth.bcrypt") as mock_bcrypt:
        mock_bcrypt.checkpw.return_value = True
        service = AuthService(ur, sr)
        await service.login("a@b.com", "pass", user_agent="TestBrowser/1.0")

    assert captured[0].user_agent == "TestBrowser/1.0"


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_list_sessions_delegates_to_repo() -> None:
    ur = _user_repo()
    sr = _session_repo()
    s1 = Session(id=1, user_id=5, token_hash="h1", expires_at=datetime.now(UTC))
    s2 = Session(id=2, user_id=5, token_hash="h2", expires_at=datetime.now(UTC))
    sr.list_by_user.return_value = [s1, s2]  # type: ignore[attr-defined]

    service = AuthService(ur, sr)
    result = await service.list_sessions(5)

    sr.list_by_user.assert_awaited_once_with(5)  # type: ignore[attr-defined]
    assert result == [s1, s2]
