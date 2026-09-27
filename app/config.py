"""Settings read from environment variables, with safe defaults for local use."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Always the same file, whichever folder the service is started from. A relative path
# would quietly create a new, empty database when started from another folder.
DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'inventory.db').as_posix()}"


def database_url() -> str:
    """Return the database connection string.

    Set DATABASE_URL to use another database, for example PostgreSQL.
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
