"""The seed dataset has the boundary cases that tests and demos rely on."""

from datetime import timedelta

from sqlalchemy import func, select

from app.models import Dealership, Vehicle, VehicleAction
from app.seed import seed
from tests.conftest import REFERENCE_DATE


def _days_in_stock_of_cars_in_stock(session):
    rows = session.scalars(select(Vehicle).where(Vehicle.sold_date.is_(None))).all()
    return {
        None if v.stock_in_date is None else (REFERENCE_DATE - v.stock_in_date).days for v in rows
    }


def test_seed_includes_the_boundary_cases(session):
    seed(session, REFERENCE_DATE)

    days = _days_in_stock_of_cars_in_stock(session)

    assert {75, 76, 89, 90, 91}.issubset(days)
    assert max(d for d in days if d is not None) >= 365  # a very old vehicle
    assert None in days  # a vehicle with no stock-in date


def test_seed_includes_a_car_that_came_back_as_a_trade_in(session):
    seed(session, REFERENCE_DATE)

    stays = session.scalars(select(Vehicle).where(Vehicle.vin == "SEED0000000000012")).all()

    assert len(stays) == 2
    assert sum(v.sold_date is None for v in stays) == 1


def test_seed_does_nothing_when_the_database_already_has_other_data(session):
    session.add(Dealership(name="Another Dealer", city="Hue"))
    session.commit()

    assert seed(session, REFERENCE_DATE) is False
    assert session.scalar(select(func.count()).select_from(Vehicle)) == 0


def test_seed_can_run_twice_without_duplicates(session):
    assert seed(session, REFERENCE_DATE) is True
    assert seed(session, REFERENCE_DATE + timedelta(days=3)) is False

    assert session.scalar(select(func.count()).select_from(Dealership)) == 3
    assert session.scalar(select(func.count()).select_from(Vehicle)) == 13
    assert session.scalar(select(func.count()).select_from(VehicleAction)) == 5
