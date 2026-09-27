"""Checks every vehicle record before it is loaded into the database.

Bad records are rejected with the vehicle and the reason, so they can be fixed at the
source (SPEC AC-2.6). Nothing is loaded if any record is bad.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VehicleRecord:
    """A vehicle as it arrives from a data source, before it is loaded."""

    vin: str
    make: str
    model: str
    model_year: int
    price: int
    stock_in_date: date | None
    sold_date: date | None = None


@dataclass(frozen=True)
class RecordProblem:
    position: int  # 1-based position in the input
    vin: str
    reason: str

    def __str__(self) -> str:
        return f"Record {self.position} (VIN {self.vin}): {self.reason}"


class DataLoadError(ValueError):
    """One or more records are bad. Nothing was loaded."""

    def __init__(self, problems: list[RecordProblem]):
        self.problems = problems
        lines = "\n".join(f"  - {p}" for p in problems)
        super().__init__(f"{len(problems)} record(s) rejected, nothing loaded:\n{lines}")


def check_record(record: VehicleRecord, reference_date: date) -> list[str]:
    """Return the reasons this record is bad. An empty list means it is fine."""
    reasons = []
    if record.stock_in_date is not None and record.stock_in_date > reference_date:
        reasons.append(
            f"stock-in date {record.stock_in_date.isoformat()} is after today "
            f"({reference_date.isoformat()})"
        )
    if record.sold_date is not None:
        if record.sold_date > reference_date:
            reasons.append(
                f"sold date {record.sold_date.isoformat()} is after today "
                f"({reference_date.isoformat()})"
            )
        if record.stock_in_date is not None and record.sold_date < record.stock_in_date:
            reasons.append(
                f"sold date {record.sold_date.isoformat()} is before the stock-in date "
                f"{record.stock_in_date.isoformat()}"
            )
    if record.price < 0:
        reasons.append(f"price {record.price} is negative")
    return reasons


def check_records(records: list[VehicleRecord], reference_date: date) -> None:
    """Raise DataLoadError listing every bad record, or return if all are fine."""
    problems = [
        RecordProblem(position, record.vin, reason)
        for position, record in enumerate(records, start=1)
        for reason in check_record(record, reference_date)
    ]
    if problems:
        raise DataLoadError(problems)
