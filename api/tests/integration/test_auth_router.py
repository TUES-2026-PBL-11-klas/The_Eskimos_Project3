"""Integration tests for the auth router — Phase 6.

Spins up a dedicated throwaway Postgres via testcontainers, runs Alembic migrations,
and exercises the full HTTP surface:

  register → login → protected routes → logout → token rejected
  duplicate email → 409
  bad credentials → 401
  no / expired token → 401
  session revocation → 404 on subsequent use
"""

from __future__ import annotations

import hashlib
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
# Helpers shared with test_users_db (copy to keep files independent)
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
# Session-scoped containers + migrated URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_users_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16", driver="asyncpg") as c:
        yield c


@pytest.fixture(scope="session")
def auth_users_db_url(auth_users_container: PostgresContainer) -> str:
    url = auth_users_container.get_connection_url()
    _run_alembic("upgrade", url)
    return url


# ---------------------------------------------------------------------------
# Per-test truncation (keep tests isolated)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _truncate(auth_users_db_url: str) -> AsyncIterator[None]:
    yield
    engine = create_async_engine(auth_users_db_url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
    await engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client with users-DB override
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(auth_users_db_url: str) -> AsyncIterator[AsyncClient]:
    from api.deps import _get_users_session
    from api.main import create_app

    engine = create_async_engine(auth_users_db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[_get_users_session] = _override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    await engine.dispose()


# ---------------------------------------------------------------------------
# Fixtures: register + login helpers
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


# ---------------------------------------------------------------------------
# Register tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_register_returns_201_with_user_fields(client: AsyncClient) -> None:
    data = await _register(client)
    assert data["email"] == "u@test.com"
    assert "id" in data
    assert "created_at" in data
    assert "password_hash" not in data


@pytest.mark.integration
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    await _register(client)
    r = await client.post("/auth/register", json={"email": "u@test.com", "password": "other"})
    assert r.status_code == 409


@pytest.mark.integration
async def test_register_password_over_72_bytes_returns_422(client: AsyncClient) -> None:
    r = await client.post("/auth/register", json={"email": "a@b.com", "password": "x" * 73})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_login_returns_token_and_expiry(client: AsyncClient) -> None:
    await _register(client)
    r = await client.post("/auth/login", json={"email": "u@test.com", "password": "pass123"})
    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert "token" in data
    assert "expires_at" in data


@pytest.mark.integration
async def test_login_bad_email_returns_401(client: AsyncClient) -> None:
    r = await client.post("/auth/login", json={"email": "no@body.com", "password": "x"})
    assert r.status_code == 401


@pytest.mark.integration
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await _register(client)
    r = await client.post("/auth/login", json={"email": "u@test.com", "password": "wrong"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Protected-route auth enforcement
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_no_token_returns_401(client: AsyncClient) -> None:
    r = await client.get("/auth/sessions")
    assert r.status_code == 401


@pytest.mark.integration
async def test_garbage_token_returns_401(client: AsyncClient) -> None:
    r = await client.get("/auth/sessions", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


@pytest.mark.integration
async def test_valid_token_accesses_sessions_list(client: AsyncClient) -> None:
    await _register(client)
    token = await _login(client)
    r = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    sessions: list[dict[str, Any]] = r.json()
    assert len(sessions) == 1
    assert "expires_at" in sessions[0]


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_logout_returns_204(client: AsyncClient) -> None:
    await _register(client)
    token = await _login(client)
    r = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204


@pytest.mark.integration
async def test_token_rejected_after_logout(client: AsyncClient) -> None:
    await _register(client)
    token = await _login(client)
    await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    r = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Session revocation
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_revoke_own_session(client: AsyncClient) -> None:
    await _register(client)
    token = await _login(client)
    sessions_r = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    session_id = sessions_r.json()[0]["id"]

    r = await client.delete(
        f"/auth/sessions/{session_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 204


@pytest.mark.integration
async def test_revoke_other_users_session_returns_404(client: AsyncClient) -> None:
    await _register(client, "a@a.com", "pass")
    await _register(client, "b@b.com", "pass")
    token_a = await _login(client, "a@a.com", "pass")
    token_b = await _login(client, "b@b.com", "pass")

    # get B's session id
    sessions_b = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token_b}"})
    session_id_b = sessions_b.json()[0]["id"]

    # A tries to revoke B's session
    r = await client.delete(
        f"/auth/sessions/{session_id_b}", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Expired session
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_expired_session_returns_401(client: AsyncClient, auth_users_db_url: str) -> None:
    await _register(client)
    token = await _login(client)

    # Manually expire the session in DB
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    engine = create_async_engine(auth_users_db_url)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE sessions SET expires_at = :past WHERE token_hash = :hash"),
            {"past": datetime(2000, 1, 1, tzinfo=UTC), "hash": token_hash},
        )
    await engine.dispose()

    r = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
