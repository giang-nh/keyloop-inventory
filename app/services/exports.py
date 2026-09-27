"""CSV exports for reporting tools such as Power BI and Excel (SPEC R4).

Days in stock and status come from the same code as the API, so the dashboard and the
API can never disagree (AC-4.1). Rows are read in batches and streamed, so a large export
does not have to fit in memory.
"""

import csv
import io
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Dealership, Vehicle, VehicleAction
from app.services.aging import days_in_stock
from app.services.inventory import describe

BATCH_SIZE = 1000

VEHICLE_COLUMNS = [
    ("vehicle_id", "Vehicle ID. One ID per stay in stock."),
    ("vin", "Vehicle Identification Number. Can repeat if a car came back."),
    ("dealership_id", "Dealership ID."),
    ("dealership_name", "Dealership name."),
    ("make", "Make."),
    ("model", "Model."),
    ("model_year", "Model year."),
    ("price", "List price, in VND."),
    ("stock_in_date", "Date the car arrived (YYYY-MM-DD). Empty if not known."),
    ("sold_date", "Date the car was sold (YYYY-MM-DD). Empty while in stock."),
    ("in_stock", "true or false."),
    (
        "days_in_stock",
        "In stock: days from arrival to today. Sold: days from arrival to the sale. "
        "Empty if the stock-in date is not known.",
    ),
    ("stock_status", "fresh, approaching, aging or unknown. Empty for sold cars."),
]

ACTION_COLUMNS = [
    ("action_id", "Action ID."),
    ("vehicle_id", "Vehicle ID."),
    ("vin", "Vehicle Identification Number."),
    ("dealership_id", "Dealership ID."),
    ("action_type", "One of the six action types."),
    ("created_at", "When the action was recorded, UTC (YYYY-MM-DDTHH:MM:SSZ)."),
    ("created_by", "The manager's name."),
    ("note", "The manager's note. Empty if none."),
]

# A cell starting with one of these can run as a formula when the file is opened in a
# spreadsheet ("CSV formula injection"). Such cells get a leading apostrophe, which makes
# the spreadsheet treat them as plain text (SYSTEM_DESIGN 5.6).
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def safe_text(value: str | None) -> str:
    if value is None:
        return ""
    return "'" + value if value.startswith(_FORMULA_START) else value


def _iso(value: date | None) -> str:
    return "" if value is None else value.isoformat()


def _utc(value: datetime) -> str:
    value = value if value.tzinfo else value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _csv_stream(header: list[str], rows: Iterator[list]) -> Iterator[str]:
    buffer = io.StringIO()
    # A byte order mark at the start tells Excel the file is UTF-8, so accented text such
    # as Vietnamese names shows correctly. Power BI reads it either way.
    buffer.write("﻿")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for count, row in enumerate(rows, start=1):
        writer.writerow(row)
        if count % BATCH_SIZE == 0:
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate()
    yield buffer.getvalue()


def _vehicle_row(vehicle: Vehicle, dealership_name: str, reference_date: date) -> list:
    if vehicle.sold_date is None:
        days, status = describe(vehicle, reference_date)
    else:
        days = days_in_stock(vehicle.stock_in_date, vehicle.sold_date)
        status = None
    return [
        vehicle.id,
        safe_text(vehicle.vin),
        vehicle.dealership_id,
        safe_text(dealership_name),
        safe_text(vehicle.make),
        safe_text(vehicle.model),
        vehicle.model_year,
        vehicle.price,
        _iso(vehicle.stock_in_date),
        _iso(vehicle.sold_date),
        "true" if vehicle.sold_date is None else "false",
        "" if days is None else days,
        "" if status is None else status.value,
    ]


def vehicles_csv(
    session_factory: sessionmaker | Callable[[], Session], reference_date: date
) -> Iterator[str]:
    """All vehicles, in stock and sold, as CSV text in chunks."""
    with session_factory() as session:
        rows = session.execute(
            select(Vehicle, Dealership.name)
            .join(Dealership, Vehicle.dealership_id == Dealership.id)
            .order_by(Vehicle.id)
            .execution_options(yield_per=BATCH_SIZE)
        )
        yield from _csv_stream(
            [name for name, _ in VEHICLE_COLUMNS],
            (_vehicle_row(vehicle, name, reference_date) for vehicle, name in rows),
        )


def actions_csv(session_factory: sessionmaker | Callable[[], Session]) -> Iterator[str]:
    """Every recorded action, as CSV text in chunks."""
    with session_factory() as session:
        rows = session.execute(
            select(VehicleAction, Vehicle.vin, Vehicle.dealership_id)
            .join(Vehicle, VehicleAction.vehicle_id == Vehicle.id)
            .order_by(VehicleAction.id)
            .execution_options(yield_per=BATCH_SIZE)
        )
        yield from _csv_stream(
            [name for name, _ in ACTION_COLUMNS],
            (
                [
                    action.id,
                    action.vehicle_id,
                    safe_text(vin),
                    dealership_id,
                    action.action_type.value,
                    _utc(action.created_at),
                    safe_text(action.created_by),
                    safe_text(action.note),
                ]
                for action, vin, dealership_id in rows
            ),
        )


def columns_description(columns: list[tuple[str, str]]) -> str:
    return "\n".join(f"- `{name}`: {meaning}" for name, meaning in columns)
