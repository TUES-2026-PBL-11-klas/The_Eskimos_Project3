"""Authentication router.

POST /auth/register   — create account, 409 on duplicate email
POST /auth/login      — issue opaque bearer token
POST /auth/logout     — revoke the caller's current session
GET  /auth/sessions   — list all active sessions for the caller
DELETE /auth/sessions/{id} — revoke a specific session belonging to the caller
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.deps import (
    AuthServiceDep,
    CurrentSessionDep,
    CurrentUserDep,
    SessionRepositoryDep,
)
from api.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    SessionSchema,
    TokenResponse,
    UserSchema,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, service: AuthServiceDep) -> UserSchema:
    try:
        user = await service.register(body.email, body.password, body.display_name)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UserSchema.model_validate(user)


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    service: AuthServiceDep,
) -> TokenResponse:
    try:
        token, expires_at = await service.login(
            body.email,
            body.password,
            user_agent=request.headers.get("User-Agent"),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(token=token, expires_at=expires_at)


@router.post("/logout", status_code=204)
async def logout(
    current_session: CurrentSessionDep,
    session_repo: SessionRepositoryDep,
) -> None:
    await session_repo.delete(current_session)


@router.get("/sessions")
async def list_sessions(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> list[SessionSchema]:
    sessions = await service.list_sessions(current_user.id)
    return [SessionSchema.model_validate(s) for s in sessions]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: int,
    current_user: CurrentUserDep,
    session_repo: SessionRepositoryDep,
) -> None:
    target = await session_repo.get(session_id)
    if target is None or target.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    await session_repo.delete(target)
