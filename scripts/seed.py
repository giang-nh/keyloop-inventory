"""Load the small seed dataset into the database.

Usage:
    python scripts/seed.py [--reference-date YYYY-MM-DD]

The database comes from DATABASE_URL (default: sqlite:///./inventory.db).
Run `alembic upgrade head` first to create the tables.
"""

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import make_engine, make_session_factory  # noqa: E402
from app.seed import seed  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the small seed dataset.")
    parser.add_argument(
        "--reference-date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="The date treated as today (default: today in UTC).",
    )
    args = parser.parse_args()

    engine = make_engine()
    with make_session_factory(engine)() as session:
        added = seed(session, args.reference_date)
    engine.dispose()
    print(
        "Seed data added."
        if added
        else "The database already has data, so nothing was changed. "
        "The seed only loads into an empty database."
    )


if __name__ == "__main__":
    main()
