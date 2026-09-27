"""Fixtures for API tests: an app on a fresh database, with "today" fixed."""

from datetime import UTC, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_now, get_reference_date
from app.main import create_app
from app.models import Dealership, Vehicle
from app.seed import seed
from tests.conftest import REFERENCE_DATE

NOW = datetime.combine(REFERENCE_DATE, time(10, 30), UTC)


def make_client(database_url: str) -> TestClient:
    app = create_app(database_url)
    app.dependency_overrides[get_reference_date] = lambda: REFERENCE_DATE
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app)


@pytest.fixture
def client(engine, database_url):
    """An app on an empty database (tables created)."""
    with make_client(database_url) as test_client:
        yield test_client


@pytest.fixture
def seeded(session):
    """The seed dataset, with "today" as the reference date."""
    seed(session, REFERENCE_DATE)
    return session


@pytest.fixture
def add_vehicle(session):
    """Add one vehicle. `days` is days in stock on the reference date."""
    dealership = Dealership(name="Test Dealership", city="Test City")
    session.add(dealership)
    session.commit()

    def _add(days=10, make="Kia", model="Seltos", price=599_000_000, sold_days_ago=None,
             dealership_id=None, vin="TESTVIN0000000001"):
        vehicle = Vehicle(
            vin=vin,
            dealership_id=dealership_id or dealership.id,
            make=make,
            model=model,
            model_year=2024,
            price=price,
            stock_in_date=None if days is None else REFERENCE_DATE - timedelta(days=days),
            sold_date=(
                None if sold_days_ago is None else REFERENCE_DATE - timedelta(days=sold_days_ago)
            ),
        )
        session.add(vehicle)
        session.commit()
        return vehicle

    _add.dealership_id = dealership.id
    return _add
