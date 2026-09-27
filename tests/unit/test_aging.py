"""The aging rule. Test names include the acceptance criterion they prove."""

from datetime import date, timedelta

import pytest

from app.services.aging import (
    FutureStockInDateError,
    StockStatus,
    days_in_stock,
    days_range_to_stock_in_dates,
    stock_in_date_range,
    stock_status,
)
from tests.conftest import REFERENCE_DATE


def arrived(days_ago: int) -> date:
    return REFERENCE_DATE - timedelta(days=days_ago)


def status_on_reference_date(days_ago: int) -> StockStatus:
    return stock_status(days_in_stock(arrived(days_ago), REFERENCE_DATE))


def test_ac_2_1_days_in_stock_counts_whole_days_to_the_reference_date():
    assert days_in_stock(arrived(0), REFERENCE_DATE) == 0
    assert days_in_stock(arrived(1), REFERENCE_DATE) == 1
    assert days_in_stock(date(2025, 1, 15), REFERENCE_DATE) == 365


def test_ac_2_1_days_in_stock_crosses_a_leap_day_correctly():
    assert days_in_stock(date(2024, 2, 28), date(2024, 3, 1)) == 2


def test_ac_2_2_day_90_is_not_aging():
    assert status_on_reference_date(90) is StockStatus.APPROACHING


def test_ac_2_2_day_91_is_aging():
    assert status_on_reference_date(91) is StockStatus.AGING


def test_ac_2_2_long_stays_are_aging():
    assert status_on_reference_date(400) is StockStatus.AGING


def test_ac_2_3_days_76_to_90_are_approaching():
    assert status_on_reference_date(76) is StockStatus.APPROACHING
    assert status_on_reference_date(89) is StockStatus.APPROACHING


def test_ac_2_4_days_0_to_75_are_fresh():
    assert status_on_reference_date(0) is StockStatus.FRESH
    assert status_on_reference_date(75) is StockStatus.FRESH


def test_ac_2_5_missing_stock_in_date_is_unknown_not_zero_days():
    assert days_in_stock(None, REFERENCE_DATE) is None
    assert stock_status(None) is StockStatus.UNKNOWN


def test_ac_2_6_stock_in_date_in_the_future_is_rejected():
    with pytest.raises(FutureStockInDateError, match="after"):
        days_in_stock(REFERENCE_DATE + timedelta(days=1), REFERENCE_DATE)


@pytest.mark.parametrize("days_ago", range(0, 400))
def test_ac_2_2_filter_ranges_agree_with_status_labels_on_every_day(days_ago):
    """ADR 0003: the date ranges used for filtering must match the labels exactly."""
    stock_in = arrived(days_ago)
    label = stock_status(days_in_stock(stock_in, REFERENCE_DATE))

    matching = []
    for status in (StockStatus.FRESH, StockStatus.APPROACHING, StockStatus.AGING):
        earliest, latest = stock_in_date_range(status, REFERENCE_DATE)
        if (earliest is None or stock_in >= earliest) and (latest is None or stock_in <= latest):
            matching.append(status)

    assert matching == [label]


def test_ac_1_6_days_range_includes_both_limits():
    earliest, latest = days_range_to_stock_in_dates(10, 20, REFERENCE_DATE)

    assert earliest == arrived(20)
    assert latest == arrived(10)


def test_unknown_status_has_no_date_range():
    with pytest.raises(ValueError):
        stock_in_date_range(StockStatus.UNKNOWN, REFERENCE_DATE)
