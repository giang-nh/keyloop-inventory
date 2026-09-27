"""Database engine and sessions."""

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import database_url


class Base(DeclarativeBase):
    """Base class for all tables."""


def make_engine(url: str | None = None) -> Engine:
    """Create an engine. SQLite gets foreign key checks switched on."""
    url = url or database_url()
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        # SQLite ignores foreign keys unless asked to check them on every connection.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
