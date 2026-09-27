"""Shared test fixtures."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (registers the tables)
from app.db import Base, make_engine, make_session_factory

# Every test uses this date as "today", so results never depend on when tests run.
REFERENCE_DATE = date(2026, 1, 15)


@pytest.fixture
def database_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"


@pytest.fixture
def engine(database_url):
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Session:
    with make_session_factory(engine)() as session:
        yield session
