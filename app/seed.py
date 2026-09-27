"""A small, fixed dataset for tests and quick checks. Prices are in VND.

Every date is set relative to a reference date, so the boundary cases (75, 76, 89, 90
and 91 days in stock) are always true on the day the seed runs. For three years of
realistic data, use the data generator instead.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ActionType, Dealership, Vehicle, VehicleAction

DEALERSHIPS = [
    ("Riverside Motors", "Ho Chi Minh City"),
    ("Harbour Auto", "Da Nang"),
    ("Lakeside Cars", "Hanoi"),
]


@dataclass(frozen=True)
class SeedVehicle:
    vin: str
    dealership: int  # position in DEALERSHIPS
    make: str
    model: str
    model_year: int
    price: int
    days_in_stock: int | None  # None means the stock-in date is missing
    sold_days_ago: int | None = None  # None means still in stock


# Each row is there for a reason, given in the comment.
VEHICLES = [
    # Arrived today.
    SeedVehicle("SEED0000000000001", 0, "Toyota", "Corolla Cross", 2025, 820_000_000, 0),
    SeedVehicle("SEED0000000000002", 0, "Honda", "CR-V", 2025, 1_029_000_000, 30),  # fresh
    # Last fresh day.
    SeedVehicle("SEED0000000000003", 1, "Hyundai", "Tucson", 2024, 769_000_000, 75),
    # First approaching.
    SeedVehicle("SEED0000000000004", 1, "Kia", "Seltos", 2024, 599_000_000, 76),
    # Approaching.
    SeedVehicle("SEED0000000000005", 0, "Toyota", "Fortuner", 2024, 1_055_000_000, 89),
    # Last day not aging.
    SeedVehicle("SEED0000000000006", 2, "Mazda", "CX-5", 2024, 749_000_000, 90),
    SeedVehicle("SEED0000000000007", 2, "Ford", "Ranger", 2024, 707_000_000, 91),  # first aging day
    SeedVehicle("SEED0000000000008", 0, "Ford", "Everest", 2023, 1_099_000_000, 120),  # aging
    # Very old.
    SeedVehicle("SEED0000000000009", 1, "Mitsubishi", "Xpander", 2023, 560_000_000, 400),
    # No stock-in date.
    SeedVehicle("SEED0000000000010", 2, "Honda", "City", 2024, 499_000_000, None),
    SeedVehicle("SEED0000000000011", 0, "Toyota", "Vios", 2024, 458_000_000, 60, 10),  # sold
    # A car that was sold and came back as a trade-in: same VIN, two stays in stock.
    SeedVehicle("SEED0000000000012", 1, "Hyundai", "Accent", 2022, 439_000_000, 500, 380),
    SeedVehicle("SEED0000000000012", 1, "Hyundai", "Accent", 2022, 320_000_000, 95),
]


def _days_before(reference_date: date, days: int | None) -> date | None:
    return None if days is None else reference_date - timedelta(days=days)


def seed(session: Session, reference_date: date) -> bool:
    """Add the seed data to an empty database.

    Returns False and changes nothing if the database already has any data: the seed data
    or other data, such as the 3-year generated dataset. Mixing the two would make both
    harder to reason about.
    """
    if session.scalar(select(func.count()).select_from(Dealership)):
        return False

    dealerships = [Dealership(name=name, city=city) for name, city in DEALERSHIPS]
    session.add_all(dealerships)

    vehicles = [
        Vehicle(
            vin=v.vin,
            dealership=dealerships[v.dealership],
            make=v.make,
            model=v.model,
            model_year=v.model_year,
            price=v.price,
            stock_in_date=_days_before(reference_date, v.days_in_stock),
            sold_date=_days_before(reference_date, v.sold_days_ago),
        )
        for v in VEHICLES
    ]
    session.add_all(vehicles)

    def at(days_ago: int) -> datetime:
        return datetime.combine(reference_date - timedelta(days=days_ago), time(9, 0), UTC)

    fortuner, everest, xpander = vehicles[4], vehicles[7], vehicles[8]
    session.add_all(
        [
            VehicleAction(vehicle=xpander, action_type=ActionType.UNDER_REVIEW,
                          created_by="Linh Tran", created_at=at(300)),
            VehicleAction(vehicle=xpander, action_type=ActionType.PRICE_REDUCTION_PLANNED,
                          note="Reduce by 5%", created_by="Linh Tran", created_at=at(200)),
            VehicleAction(vehicle=xpander, action_type=ActionType.SEND_TO_AUCTION,
                          created_by="Minh Pham", created_at=at(5)),
            VehicleAction(vehicle=everest, action_type=ActionType.MARKETING_PROMOTION,
                          note="Feature in weekend campaign", created_by="An Nguyen",
                          created_at=at(20)),
            VehicleAction(vehicle=fortuner, action_type=ActionType.UNDER_REVIEW,
                          created_by="An Nguyen", created_at=at(2)),
        ]
    )
    session.commit()
    return True
