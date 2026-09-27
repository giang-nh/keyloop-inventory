"""The aging rule: how long a car has been in stock, and what that means.

This module is plain Python. It has no web or database code, so the rule can be read
and tested on its own. "Today" is always passed in as `reference_date`; nothing here
reads the clock (CLAUDE.md, SPEC AC-2.1).

Stock status by days in stock (SPEC section 2, step 2):

    fresh        0 to 75
    approaching  76 to 90
    aging        more than 90
    unknown      no stock-in date
"""

from datetime import date, timedelta
from enum import StrEnum

AGING_AFTER_DAYS = 90
"""A car with more than this many days in stock is aging. Day 90 is not; day 91 is."""

APPROACHING_FROM_DAYS = 76
"""The first day of the early-warning window (SPEC D-4)."""


class StockStatus(StrEnum):
    FRESH = "fresh"
    APPROACHING = "approaching"
    AGING = "aging"
    UNKNOWN = "unknown"


# Statuses for which a manager may record an action (SPEC D-8).
ACTIONABLE_STATUSES = frozenset({StockStatus.APPROACHING, StockStatus.AGING})


class FutureStockInDateError(ValueError):
    """The stock-in date is after the reference date, which cannot be true."""


def days_in_stock(stock_in_date: date | None, reference_date: date) -> int | None:
    """Whole days from the stock-in date to the reference date.

    Returns None when the stock-in date is missing. A missing date is unknown, never
    zero (SPEC AC-2.5). A date in the future is bad data and raises an error.
    """
    if stock_in_date is None:
        return None
    if stock_in_date > reference_date:
        raise FutureStockInDateError(
            f"Stock-in date {stock_in_date.isoformat()} is after {reference_date.isoformat()}."
        )
    return (reference_date - stock_in_date).days


def stock_status(days: int | None) -> StockStatus:
    """The status for a car in stock with this many days in stock."""
    if days is None:
        return StockStatus.UNKNOWN
    if days > AGING_AFTER_DAYS:
        return StockStatus.AGING
    if days >= APPROACHING_FROM_DAYS:
        return StockStatus.APPROACHING
    return StockStatus.FRESH


def stock_in_date_range(
    status: StockStatus, reference_date: date
) -> tuple[date | None, date | None]:
    """The stock-in dates that give this status on the reference date.

    Returns (earliest, latest), both included; None means "no limit". Used to filter in
    the database, so it must agree with `stock_status` at every boundary. A test checks
    that it does. Not defined for UNKNOWN, which means "no stock-in date".
    """
    if status is StockStatus.UNKNOWN:
        raise ValueError("UNKNOWN has no date range; filter on a missing stock-in date instead.")
    if status is StockStatus.AGING:
        return None, reference_date - timedelta(days=AGING_AFTER_DAYS + 1)
    if status is StockStatus.APPROACHING:
        return (
            reference_date - timedelta(days=AGING_AFTER_DAYS),
            reference_date - timedelta(days=APPROACHING_FROM_DAYS),
        )
    return reference_date - timedelta(days=APPROACHING_FROM_DAYS - 1), reference_date


def days_range_to_stock_in_dates(
    min_days: int | None, max_days: int | None, reference_date: date
) -> tuple[date | None, date | None]:
    """Turn "between min and max days in stock" (both included) into stock-in dates."""
    earliest = None if max_days is None else reference_date - timedelta(days=max_days)
    latest = None if min_days is None else reference_date - timedelta(days=min_days)
    return earliest, latest
