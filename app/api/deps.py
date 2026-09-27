"""Things routes need: a database session, and the date and time to treat as "now".

Tests replace get_reference_date and get_now, so results never depend on the real clock.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime

from fastapi import Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def get_reference_date() -> date:
    """Today, in UTC (SPEC D-2)."""
    return datetime.now(UTC).date()


def get_now() -> datetime:
    """The current time, in UTC. Used to stamp new actions (SPEC D-12)."""
    return datetime.now(UTC)
