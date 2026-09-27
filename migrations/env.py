"""Alembic migration environment.

The database URL comes from app.config, so migrations and the service always use the
same database. Tests can pass their own URL with the "sqlalchemy.url" option.
"""

from logging.config import fileConfig

from alembic import context

import app.models  # noqa: F401  (registers the tables on Base.metadata)
from app.config import database_url
from app.db import Base, make_engine

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    return config.get_main_option("sqlalchemy.url") or database_url()


def run_migrations_offline() -> None:
    """Write the SQL to the screen instead of running it."""
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run the migrations against the database."""
    engine = make_engine(_url())
    with engine.connect() as connection:
        # Batch mode lets SQLite change existing tables, which it cannot do directly.
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
