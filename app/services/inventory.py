"""Reading vehicles from the database.

Filters run in the database: status and age are turned into stock-in date ranges
(ADR 0003), so the database can use its indexes instead of the service loading every car.
"""

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Vehicle, VehicleAction
from app.services.aging import (
    FutureStockInDateError,
    StockStatus,
    days_in_stock,
    days_range_to_stock_in_dates,
    stock_in_date_range,
    stock_status,
)

logger = logging.getLogger("inventory")


# The order of the vehicle list (AC-1.9).
LIST_ORDER = (
    # No stock-in date first, so missing data gets noticed and fixed.
    Vehicle.stock_in_date.is_(None).desc(),
    # Then the oldest (most days in stock) first.
    Vehicle.stock_in_date.asc(),
    # Then by ID, so paging never repeats or skips a vehicle. Without this, the database
    # may return ties in any order, and each page request could see a different order.
    Vehicle.id.asc(),
)


@dataclass(frozen=True)
class VehicleFilters:
    dealership_id: int | None = None
    make: str | None = None
    model: str | None = None
    min_days: int | None = None
    max_days: int | None = None
    status: StockStatus | None = None


@dataclass(frozen=True)
class VehicleView:
    """A vehicle with the values worked out for the reference date."""

    vehicle: Vehicle
    days_in_stock: int | None
    stock_status: StockStatus | None
    latest_action: VehicleAction | None


def _between(query: Select, earliest: date | None, latest: date | None) -> Select:
    if earliest is not None:
        query = query.where(Vehicle.stock_in_date >= earliest)
    if latest is not None:
        query = query.where(Vehicle.stock_in_date <= latest)
    return query


def _filtered(filters: VehicleFilters, reference_date: date) -> Select:
    query = select(Vehicle).where(Vehicle.sold_date.is_(None))  # in stock only (AC-1.1)
    if filters.dealership_id is not None:
        query = query.where(Vehicle.dealership_id == filters.dealership_id)
    # Exact match that ignores case (AC-1.4, AC-1.5), using the lower() index.
    if filters.make is not None:
        query = query.where(func.lower(Vehicle.make) == filters.make.lower())
    if filters.model is not None:
        query = query.where(func.lower(Vehicle.model) == filters.model.lower())
    if filters.min_days is not None or filters.max_days is not None:
        query = _between(
            query, *days_range_to_stock_in_dates(filters.min_days, filters.max_days, reference_date)
        )
        # A stock-in date in the future has no days in stock, so it never matches (AC-2.9).
        query = query.where(Vehicle.stock_in_date <= reference_date)
    if filters.status is StockStatus.UNKNOWN:
        # Unknown means the date is missing or cannot be right (SPEC D-6, AC-2.9).
        query = query.where(
            or_(Vehicle.stock_in_date.is_(None), Vehicle.stock_in_date > reference_date)
        )
    elif filters.status is not None:
        query = _between(query, *stock_in_date_range(filters.status, reference_date))
    return query


def latest_actions(session: Session, vehicle_ids: list[int]) -> dict[int, VehicleAction]:
    """The most recent action for each of these vehicles (ADR 0004)."""
    if not vehicle_ids:
        return {}
    newest_first = (
        func.row_number()
        .over(
            partition_by=VehicleAction.vehicle_id,
            order_by=(VehicleAction.created_at.desc(), VehicleAction.id.desc()),
        )
        .label("position")
    )
    ranked = (
        select(VehicleAction.id, newest_first)
        .where(VehicleAction.vehicle_id.in_(vehicle_ids))
        .subquery()
    )
    actions = session.scalars(
        select(VehicleAction).join(ranked, ranked.c.id == VehicleAction.id).where(
            ranked.c.position == 1
        )
    )
    return {action.vehicle_id: action for action in actions}


def describe(vehicle: Vehicle, reference_date: date) -> tuple[int | None, StockStatus | None]:
    """Days in stock and status for one vehicle. Sold vehicles have no status (AC-2.7)."""
    if vehicle.sold_date is not None:
        return None, None
    try:
        days = days_in_stock(vehicle.stock_in_date, reference_date)
    except FutureStockInDateError:
        # The loader stops this, but the list must not fail for everyone if a bad record
        # gets in some other way. Show it as unknown and flag it in the logs.
        logger.warning("future_stock_in_date", extra={"fields": {"vehicle_id": vehicle.id}})
        return None, StockStatus.UNKNOWN
    return days, stock_status(days)


def list_vehicles(
    session: Session,
    filters: VehicleFilters,
    reference_date: date,
    limit: int,
    offset: int,
) -> tuple[list[VehicleView], int]:
    """One page of vehicles in stock, and the total that match the filters."""
    query = _filtered(filters, reference_date)
    total = session.scalar(select(func.count()).select_from(query.subquery()))

    page = session.scalars(
        query.options(joinedload(Vehicle.dealership))
        .order_by(*LIST_ORDER)
        .limit(limit)
        .offset(offset)
    ).all()

    latest = latest_actions(session, [v.id for v in page])
    views = [VehicleView(v, *describe(v, reference_date), latest.get(v.id)) for v in page]
    return views, total


def get_vehicle(session: Session, vehicle_id: int, reference_date: date) -> VehicleView | None:
    vehicle = session.get(Vehicle, vehicle_id, options=[joinedload(Vehicle.dealership)])
    if vehicle is None:
        return None
    return VehicleView(
        vehicle,
        *describe(vehicle, reference_date),
        latest_actions(session, [vehicle.id]).get(vehicle.id),
    )


def summary(session: Session, reference_date: date, dealership_id: int | None) -> dict:
    """Counts and values of aging and approaching stock (AC-2.8), in one query."""
    _, aging_latest = stock_in_date_range(StockStatus.AGING, reference_date)
    approaching_earliest, approaching_latest = stock_in_date_range(
        StockStatus.APPROACHING, reference_date
    )
    is_aging = Vehicle.stock_in_date <= aging_latest
    is_approaching = Vehicle.stock_in_date.between(approaching_earliest, approaching_latest)

    query = select(
        func.count(),
        func.coalesce(func.sum(case((is_aging, 1), else_=0)), 0),
        func.coalesce(func.sum(case((is_approaching, 1), else_=0)), 0),
        func.coalesce(func.sum(case((is_aging, Vehicle.price), else_=0)), 0),
        func.coalesce(func.sum(case((is_approaching, Vehicle.price), else_=0)), 0),
    ).where(Vehicle.sold_date.is_(None))
    if dealership_id is not None:
        query = query.where(Vehicle.dealership_id == dealership_id)

    in_stock, aging, approaching, aging_value, approaching_value = session.execute(query).one()
    return {
        "dealership_id": dealership_id,
        "vehicles_in_stock": in_stock,
        "aging_count": aging,
        "approaching_count": approaching,
        "aging_value": aging_value,
        "approaching_value": approaching_value,
    }
