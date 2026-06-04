"""FastAPI application factory and lifespan.

The lifespan opens the database engine(s) on startup and disposes them on shutdown so
connections are released cleanly. In Phase 0 only the events engine is wired; the users engine
is added in Phase 4. Routers are registered here, keeping the app factory the single place that
assembles the HTTP surface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.db.events import events_engine
from api.db.users import users_engine
from api.routers import events, system


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage engine lifecycle: dispose both DB pools on shutdown."""
    try:
        yield
    finally:
        await events_engine.dispose()
        await users_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="EventHub API", version="0.1.0", lifespan=lifespan)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(system.router)
    app.include_router(events.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)  # noqa: S104
