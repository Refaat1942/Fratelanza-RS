"""Alembic environment.

Two entry points:
* ``alembic upgrade head`` (CLI) — connects with ``DATABASE_URL_SYNC``.
* ``app.core.migrations.run_migrations`` (app startup) — passes an open connection via
  ``config.attributes["connection"]`` so migrations run inside the startup advisory lock.
"""

from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401  (register every model on Base.metadata)
from app.core.config import settings
from app.core.database import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL_SYNC, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(settings.DATABASE_URL_SYNC)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
