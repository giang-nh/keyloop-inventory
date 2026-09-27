"""Request and response models. Their descriptions become the API documentation."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ActionType
from app.services.aging import StockStatus


class ErrorDetail(BaseModel):
    field: str = Field(description="The input field with the problem.")
    problem: str


class ErrorInfo(BaseModel):
    code: str = Field(description="A stable code for programs, for example vehicle_not_found.")
    message: str = Field(description="What went wrong and what to do next, for people.")
    details: list[ErrorDetail] = Field(description="One entry per invalid field, if any.")


class ErrorResponse(BaseModel):
    """The shape of every error response."""

    error: ErrorInfo


def error_responses(*status_codes: int) -> dict:
    """Document these error statuses with the real error shape in the API contract."""
    meaning = {
        404: "Not found.",
        422: "The input is not valid, or the request is not allowed for this vehicle.",
    }
    return {code: {"model": ErrorResponse, "description": meaning[code]} for code in status_codes}


class DealershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    action_type: ActionType
    note: str | None
    created_by: str = Field(description="The name of the manager who recorded the action.")
    created_at: datetime = Field(description="When the action was recorded, in UTC.")

    @field_validator("created_at")
    @classmethod
    def _as_utc(cls, value: datetime) -> datetime:
        # SQLite gives back times without a time zone; they are stored in UTC.
        return value if value.tzinfo else value.replace(tzinfo=UTC)


class ActionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: ActionType = Field(description="What the manager plans to do (SPEC D-7).")
    created_by: str = Field(
        min_length=1, max_length=100, description="The manager's name. There is no login."
    )
    note: str | None = Field(default=None, max_length=500, description="Optional detail.")

    @field_validator("created_by")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class VehicleOut(BaseModel):
    id: int
    vin: str
    dealership_id: int
    dealership_name: str
    make: str
    model: str
    model_year: int
    price: int = Field(description="List price, in whole currency units.")
    stock_in_date: date | None = Field(description="Empty when the date is not known.")
    sold_date: date | None = Field(description="Empty while the vehicle is in stock.")
    days_in_stock: int | None = Field(
        description="Whole days from the stock-in date to today (UTC). "
        "Empty when the stock-in date is not known."
    )
    stock_status: StockStatus | None = Field(
        description="fresh (0-75 days), approaching (76-90), aging (over 90), or unknown "
        "(no stock-in date). Empty for sold vehicles."
    )
    latest_action: ActionOut | None = Field(description="The most recent action, if any.")


class VehiclePage(BaseModel):
    items: list[VehicleOut]
    total: int = Field(description="How many vehicles match the filters, across all pages.")
    limit: int
    offset: int


class InventorySummary(BaseModel):
    dealership_id: int | None = Field(description="Empty when the summary covers all dealerships.")
    vehicles_in_stock: int
    aging_count: int
    approaching_count: int
    aging_value: int = Field(description="Total list price of aging vehicles.")
    approaching_value: int = Field(description="Total list price of approaching vehicles.")
