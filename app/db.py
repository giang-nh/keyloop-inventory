"""Database engine and sessions."""

from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import PROJECT_ROOT, database_url


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


def expected_schema_version() -> str:
    """The newest migration in the repository."""
    return ScriptDirectory(str(PROJECT_ROOT / "migrations")).get_current_head()


def current_schema_version(engine: Engine) -> str | None:
    """The migration the database is at, or None if it has never been migrated."""
    with engine.connect() as connection:
        if not engine.dialect.has_table(connection, "alembic_version"):
            return None
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
