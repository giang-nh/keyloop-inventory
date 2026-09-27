"""Generate three years of simulated dealership data and load it into the database.

The rules are in docs/DATA_SIMULATION.md. The data is for demos only: every pattern in it
comes from those rules, not from real dealerships.

Usage:
    python scripts/generate_data.py [--reference-date YYYY-MM-DD] [--seed 42] [--replace]

The database comes from DATABASE_URL (default: sqlite:///./inventory.db).
Run `alembic upgrade head` first to create the tables.
"""

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, func, select  # noqa: E402

from app.db import make_engine, make_session_factory  # noqa: E402
from app.models import Dealership, Vehicle, VehicleAction  # noqa: E402
from app.services.loading import DataLoadError  # noqa: E402
from app.simulation import generate, load  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate three years of simulated data.")
    parser.add_argument(
        "--reference-date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="The last day of the data, treated as today (default: today in UTC).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    parser.add_argument(
        "--replace", action="store_true", help="Delete all existing data first."
    )
    args = parser.parse_args()

    engine = make_engine()
    with make_session_factory(engine)() as session:
        existing = session.scalar(select(func.count()).select_from(Vehicle))
        if existing and not args.replace:
            print(f"The database already has {existing} vehicles. "
                  "Use --replace to delete them and load new data.")
            return 1
        if args.replace:
            for table in (VehicleAction, Vehicle, Dealership):
                session.execute(delete(table))
            session.commit()

        dataset = generate(args.reference_date, args.seed)
        try:
            load(session, dataset)
        except DataLoadError as error:
            print(error)
            return 1

    engine.dispose()
    in_stock = sum(v.record.sold_date is None for v in dataset.vehicles)
    actions = sum(len(v.actions) for v in dataset.vehicles)
    print(f"Loaded {len(dataset.vehicles)} vehicles ({in_stock} in stock) and {actions} actions "
          f"for 3 years up to {args.reference_date.isoformat()} (seed {args.seed}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
