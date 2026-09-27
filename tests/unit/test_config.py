"""Settings."""

from pathlib import Path

from app.config import DEFAULT_DATABASE_URL, PROJECT_ROOT


def test_default_database_is_in_the_project_folder_not_the_current_folder():
    """Found in the hidden-decisions audit (#19): a relative path created a new, empty
    database when the service was started from another folder."""
    path = Path(DEFAULT_DATABASE_URL.removeprefix("sqlite:///"))

    assert path.is_absolute()
    assert path.parent == PROJECT_ROOT
