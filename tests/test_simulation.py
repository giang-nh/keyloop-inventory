"""The 3-year simulated dataset follows the rules in docs/DATA_SIMULATION.md."""

from collections import Counter, defaultdict
from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.models import Vehicle, VehicleAction
from app.services.aging import APPROACHING_FROM_DAYS
from app.simulation import generate, load

REFERENCE = date(2026, 9, 27)


@pytest.fixture(scope="module")
def data():
    return generate(REFERENCE, seed=42)


def in_stock(data):
    return [v for v in data.vehicles if v.record.sold_date is None]


def test_same_seed_gives_the_same_data(data):
    again = generate(REFERENCE, seed=42)

    assert [v.record for v in again.vehicles] == [v.record for v in data.vehicles]
    assert [v.actions for v in again.vehicles] == [v.actions for v in data.vehicles]


def test_a_different_seed_gives_different_data(data):
    other = generate(REFERENCE, seed=7)

    assert [v.record for v in other.vehicles[:50]] != [v.record for v in data.vehicles[:50]]


def test_covers_three_years_up_to_the_reference_date(data):
    arrivals = [v.record.stock_in_date for v in data.vehicles if v.record.stock_in_date]

    assert min(arrivals) <= REFERENCE - timedelta(days=3 * 365)
    assert max(arrivals) <= REFERENCE


def test_no_sale_before_arrival_or_after_the_reference_date(data):
    for v in data.vehicles:
        r = v.record
        if r.sold_date is not None:
            assert r.stock_in_date <= r.sold_date <= REFERENCE


def test_every_action_happens_while_the_car_is_in_stock_and_at_least_76_days_old(data):
    for v in data.vehicles:
        for action in v.actions:
            day = action.created_at.date()
            assert (day - v.record.stock_in_date).days >= APPROACHING_FROM_DAYS
            assert day <= REFERENCE
            if v.record.sold_date is not None:
                assert day < v.record.sold_date


def test_counts_are_in_realistic_ranges(data):
    stock = in_stock(data)
    days = [(REFERENCE - v.record.stock_in_date).days for v in stock if v.record.stock_in_date]
    aging_share = sum(d > 90 for d in days) / len(days)
    sold_share = 1 - len(stock) / len(data.vehicles)

    assert 5_000 <= len(data.vehicles) <= 15_000
    assert 200 <= len(stock) <= 800
    assert 0.03 <= aging_share <= 0.30
    assert sold_share >= 0.85


def test_every_action_type_appears(data):
    types = Counter(a.action_type for v in data.vehicles for a in v.actions)

    assert len(types) == 6


def test_trade_ins_come_back_after_they_were_sold(data):
    stays = defaultdict(list)
    for v in data.vehicles:
        stays[v.record.vin].append(v.record)
    returned = [s for s in stays.values() if len(s) > 1]

    assert returned
    for records in returned:
        records.sort(key=lambda r: r.stock_in_date or REFERENCE)
        for earlier, later in zip(records, records[1:], strict=False):
            assert earlier.sold_date is not None
            assert later.stock_in_date > earlier.sold_date


def test_some_cars_in_stock_have_no_stock_in_date_and_no_actions(data):
    missing = [v for v in data.vehicles if v.record.stock_in_date is None]

    assert missing
    assert all(v.record.sold_date is None and not v.actions for v in missing)


def test_the_dataset_loads_through_the_normal_loader_checks(session, data):
    load(session, data)

    assert session.scalar(select(func.count()).select_from(Vehicle)) == len(data.vehicles)
    assert session.scalar(select(func.count()).select_from(VehicleAction)) == sum(
        len(v.actions) for v in data.vehicles
    )
