"""Shared test fixtures."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (registers the tables)
from app.db import Base, expected_schema_version, make_engine, make_session_factory

# Every test uses this date as "today", so results never depend on when tests run.
REFERENCE_DATE = date(2026, 1, 15)


@pytest.fixture
def database_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"


@pytest.fixture
def engine(database_url):
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    # Mark the database as migrated, as `alembic upgrade head` would. Creating the tables
    # straight from the models is much faster than running migrations in every test;
    # tests/test_migrations.py checks that the migrations build the same tables.
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        connection.execute(
            text("INSERT INTO alembic_version VALUES (:v)"), {"v": expected_schema_version()}
        )
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Session:
    with make_session_factory(engine)() as session:
        yield session
