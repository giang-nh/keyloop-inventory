"""Recording and reading actions on vehicles.

The history is append-only: this module only ever inserts rows. There is no code that
changes or deletes an action (SPEC AC-3.6).
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ActionType, Vehicle, VehicleAction
from app.services.aging import ACTIONABLE_STATUSES, APPROACHING_FROM_DAYS
from app.services.inventory import describe


class VehicleNotFoundError(LookupError):
    pass


class ActionNotAllowedError(ValueError):
    """The vehicle cannot get an action today. The message says why and what to do."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _check_allowed(vehicle: Vehicle, reference_date: date) -> None:
    if vehicle.sold_date is not None:
        raise ActionNotAllowedError(
            "vehicle_sold",
            f"Vehicle {vehicle.id} was sold on {vehicle.sold_date.isoformat()}. "
            "Actions can only be recorded for vehicles in stock.",
        )
    days, status = describe(vehicle, reference_date)
    if status in ACTIONABLE_STATUSES:
        return
    if vehicle.stock_in_date is not None and vehicle.stock_in_date > reference_date:
        raise ActionNotAllowedError(
            "vehicle_stock_in_date_invalid",
            f"Vehicle {vehicle.id} has a stock-in date in the future "
            f"({vehicle.stock_in_date.isoformat()}), which cannot be right. "
            "Fix its stock-in date first.",
        )
    if days is None:
        raise ActionNotAllowedError(
            "vehicle_stock_in_date_unknown",
            f"Vehicle {vehicle.id} has no stock-in date, so we cannot tell how long it has "
            "been in stock. Fix its stock-in date first.",
        )
    raise ActionNotAllowedError(
        "vehicle_not_eligible",
        f"Vehicle {vehicle.id} has been in stock for {days} days. Actions can only be "
        f"recorded for vehicles in stock for {APPROACHING_FROM_DAYS} days or more.",
    )


def record_action(
    session: Session,
    vehicle_id: int,
    action_type: ActionType,
    created_by: str,
    note: str | None,
    reference_date: date,
    now: datetime,
) -> VehicleAction:
    """Save a new action. The time is set here, never by the client (SPEC D-12)."""
    vehicle = session.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise VehicleNotFoundError(vehicle_id)
    _check_allowed(vehicle, reference_date)

    action = VehicleAction(
        vehicle_id=vehicle.id,
        action_type=action_type,
        created_by=created_by,
        note=note,
        created_at=now,
    )
    session.add(action)
    session.commit()
    return action


def list_actions(session: Session, vehicle_id: int) -> list[VehicleAction]:
    """A vehicle's full history, newest first (SPEC AC-3.5)."""
    if session.get(Vehicle, vehicle_id) is None:
        raise VehicleNotFoundError(vehicle_id)
    return list(
        session.scalars(
            select(VehicleAction)
            .where(VehicleAction.vehicle_id == vehicle_id)
            .order_by(VehicleAction.created_at.desc(), VehicleAction.id.desc())
        )
    )
