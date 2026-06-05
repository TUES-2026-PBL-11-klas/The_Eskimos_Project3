"""FastAPI application factory and lifespan.

The lifespan configures structured JSON logging, then opens the database engine(s) on startup
and disposes them on shutdown so connections are released cleanly. Prometheus instrumentation
is wired here, as is a central exception-handler layer that maps every domain error to the
correct HTTP status without leaking stack traces to clients.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from api.config import settings
from api.db.events import events_engine
from api.db.users import users_engine
from api.domain.exceptions import (
    AlreadySavedError,
    EventHubError,
    EventNotFoundError,
    InvalidCredentialsError,
    ReminderNotFoundError,
    UserAlreadyExistsError,
)
from api.routers import auth, events, me, system


def _configure_logging() -> None:
    """Wire structlog to emit JSON lines to stdout; underlying stdlib level from settings."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ── Central exception handlers — domain errors → HTTP, no internal details exposed ──────────

async def _on_event_not_found(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Event not found"})


async def _on_reminder_not_found(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Reminder not found"})


async def _on_user_already_exists(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Account already exists"})


async def _on_already_saved(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Event already saved"})


async def _on_invalid_credentials(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})


async def _on_eventhub_error(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for any unhandled EventHubError subclass."""
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _configure_logging()
    try:
        yield
    finally:
        await events_engine.dispose()
        await users_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="EventHub API", version="0.1.0", lifespan=lifespan)

    # Prometheus — adds GET /metrics before any middleware so it's always reachable.
    Instrumentator().instrument(app).expose(app)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Specific handlers first so Starlette's MRO walk finds them before the catch-all.
    app.add_exception_handler(EventNotFoundError, _on_event_not_found)
    app.add_exception_handler(ReminderNotFoundError, _on_reminder_not_found)
    app.add_exception_handler(UserAlreadyExistsError, _on_user_already_exists)
    app.add_exception_handler(AlreadySavedError, _on_already_saved)
    app.add_exception_handler(InvalidCredentialsError, _on_invalid_credentials)
    app.add_exception_handler(EventHubError, _on_eventhub_error)

    app.include_router(system.router)
    app.include_router(events.router)
    app.include_router(auth.router)
    app.include_router(me.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)  # noqa: S104
