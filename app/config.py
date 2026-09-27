"""Settings read from environment variables, with safe defaults for local use."""

import os

DEFAULT_DATABASE_URL = "sqlite:///./inventory.db"


def database_url() -> str:
    """Return the database connection string.

    Set DATABASE_URL to use another database, for example PostgreSQL.
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
