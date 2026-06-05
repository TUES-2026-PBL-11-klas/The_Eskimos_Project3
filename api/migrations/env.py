"""Alembic async environment for the users database.

Migrations here apply only to the users DB (owned by this service). The events DB
schema is owned by the ingestion service and is never touched here.

The URL is pulled from ``api.config.settings`` so the same migration can run
against any environment by setting ``USERS_DB_URL`` in the environment — no
hardcoded credentials in code.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from api.config import settings
from api.db.models.users import UsersBase

config = context.config
config.set_main_option("sqlalchemy.url", settings.users_db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = UsersBase.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
