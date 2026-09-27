"""Database tables.

We store facts only: when a car arrived, when it was sold, and what was done about it.
Days in stock, stock status and the latest action are worked out when someone asks
(ADR 0003, ADR 0004), so they are not stored here.
"""

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ActionType(StrEnum):
    """The six action types a manager can record (SPEC D-7)."""

    PRICE_REDUCTION_PLANNED = "PRICE_REDUCTION_PLANNED"
    MARKETING_PROMOTION = "MARKETING_PROMOTION"
    TRANSFER_TO_ANOTHER_DEALERSHIP = "TRANSFER_TO_ANOTHER_DEALERSHIP"
    SEND_TO_AUCTION = "SEND_TO_AUCTION"
    UNDER_REVIEW = "UNDER_REVIEW"
    OTHER = "OTHER"


class Dealership(Base):
    __tablename__ = "dealership"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="dealership")


class Vehicle(Base):
    """One stay in stock for one car.

    A car that is sold and later comes back (for example as a trade-in) gets a new
    record, so the VIN is not unique (SPEC D-11). A car is in stock while sold_date is
    empty; there is no separate status column that could disagree with it.
    """

    __tablename__ = "vehicle"

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(String(17))
    dealership_id: Mapped[int] = mapped_column(ForeignKey("dealership.id"))
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    model_year: Mapped[int] = mapped_column(Integer)
    # List price in VND, a whole number. VND has no smaller unit in use, and whole
    # numbers avoid rounding differences between databases.
    price: Mapped[int] = mapped_column(Integer)
    # May be empty: the car is then shown with the status "unknown" (SPEC D-6).
    stock_in_date: Mapped[date | None] = mapped_column(Date)
    # Empty while the car is in stock.
    sold_date: Mapped[date | None] = mapped_column(Date)

    dealership: Mapped[Dealership] = relationship(back_populates="vehicles")
    actions: Mapped[list["VehicleAction"]] = relationship(back_populates="vehicle")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_vehicle_price_not_negative"),
        CheckConstraint(
            "sold_date IS NULL OR stock_in_date IS NULL OR sold_date >= stock_in_date",
            name="ck_vehicle_sold_after_stock_in",
        ),
        # The main list: one dealership, in stock, by age.
        Index("ix_vehicle_dealership_sold_stock_in", "dealership_id", "sold_date", "stock_in_date"),
        # Filters by age and status across all dealerships.
        Index("ix_vehicle_stock_in_date", "stock_in_date"),
        # Make and model filters ignore upper and lower case, so the index is on the
        # lower-case values. The same expression works in SQLite and PostgreSQL.
        Index("ix_vehicle_make_model_lower", func.lower(make), func.lower(model)),
        # Every stay in stock for one car. Not unique on purpose (SPEC D-11).
        Index("ix_vehicle_vin", "vin"),
    )


class VehicleAction(Base):
    """A status or planned action recorded by a manager.

    Append-only: the service never updates or deletes these rows (SPEC AC-3.6).
    """

    __tablename__ = "vehicle_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicle.id"))
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, native_enum=False, create_constraint=True, length=40,
             name="action_type")
    )
    note: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[str] = mapped_column(String(100))
    # Always UTC, set by the service when the action is saved (SPEC D-12).
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    vehicle: Mapped[Vehicle] = relationship(back_populates="actions")

    __table_args__ = (
        # A vehicle's history, newest first, and its latest action.
        Index("ix_vehicle_action_vehicle_created", "vehicle_id", "created_at"),
    )
