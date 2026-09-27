"""The data loader rejects bad records and says which one and why."""

from datetime import timedelta

import pytest

from app.services.loading import DataLoadError, VehicleRecord, check_record, check_records
from tests.conftest import REFERENCE_DATE


def record(**changes) -> VehicleRecord:
    fields = dict(
        vin="TESTVIN0000000001",
        make="Kia",
        model="Seltos",
        model_year=2024,
        price=24_000,
        stock_in_date=REFERENCE_DATE - timedelta(days=10),
        sold_date=None,
    )
    fields.update(changes)
    return VehicleRecord(**fields)


def test_a_good_record_has_no_problems():
    assert check_record(record(), REFERENCE_DATE) == []


def test_a_missing_stock_in_date_is_allowed():
    assert check_record(record(stock_in_date=None), REFERENCE_DATE) == []


def test_ac_2_6_loader_rejects_a_stock_in_date_after_the_reference_date():
    bad = record(vin="FUTUREVIN00000001", stock_in_date=REFERENCE_DATE + timedelta(days=1))

    with pytest.raises(DataLoadError) as error:
        check_records([record(), bad], REFERENCE_DATE)

    message = str(error.value)
    assert "Record 2" in message
    assert "FUTUREVIN00000001" in message
    assert "stock-in date" in message and "after today" in message


def test_loader_rejects_a_sale_before_arrival():
    bad = record(sold_date=REFERENCE_DATE - timedelta(days=20))

    assert any("before the stock-in date" in r for r in check_record(bad, REFERENCE_DATE))


def test_loader_rejects_a_sale_in_the_future():
    bad = record(sold_date=REFERENCE_DATE + timedelta(days=1))

    assert any("sold date" in r and "after today" in r for r in check_record(bad, REFERENCE_DATE))


def test_loader_rejects_a_price_that_is_not_a_whole_number():
    bad = record(price=529_000_000.0)

    assert any("not a whole number" in r for r in check_record(bad, REFERENCE_DATE))


def test_loader_reports_every_bad_record_not_just_the_first():
    bad = [record(price=-1), record(stock_in_date=REFERENCE_DATE + timedelta(days=5))]

    with pytest.raises(DataLoadError) as error:
        check_records(bad, REFERENCE_DATE)

    assert len(error.value.problems) == 2
