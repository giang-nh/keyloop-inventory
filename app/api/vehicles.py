"""Vehicle routes: the list of vehicles in stock, and one vehicle."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_reference_date, get_session
from app.api.errors import ApiError
from app.api.schemas import ActionOut, VehicleOut, VehiclePage, error_responses
from app.services.aging import StockStatus
from app.services.inventory import VehicleFilters, VehicleView, get_vehicle, list_vehicles

router = APIRouter(
    prefix="/api/v1/vehicles", tags=["Vehicles"], responses=error_responses(422)
)

MAX_PAGE_SIZE = 200


def to_vehicle_out(view: VehicleView) -> VehicleOut:
    v = view.vehicle
    return VehicleOut(
        id=v.id,
        vin=v.vin,
        dealership_id=v.dealership_id,
        dealership_name=v.dealership.name,
        make=v.make,
        model=v.model,
        model_year=v.model_year,
        price=v.price,
        stock_in_date=v.stock_in_date,
        sold_date=v.sold_date,
        days_in_stock=view.days_in_stock,
        stock_status=view.stock_status,
        latest_action=ActionOut.model_validate(view.latest_action) if view.latest_action else None,
    )


@router.get(
    "",
    response_model=VehiclePage,
    summary="List vehicles in stock",
    description=(
        "Vehicles that are in stock, with filters. Vehicles with no stock-in date come first, "
        "then the most days in stock, then by ID. All filters must match."
    ),
)
def list_vehicles_route(
    session: Annotated[Session, Depends(get_session)],
    reference_date: Annotated[date, Depends(get_reference_date)],
    dealership_id: Annotated[int | None, Query(ge=1, description="Only this dealership.")] = None,
    make: Annotated[
        str | None,
        Query(max_length=50, description="Exact make, any case. 'toyota' finds 'Toyota'."),
    ] = None,
    model: Annotated[
        str | None, Query(max_length=50, description="Exact model, any case.")
    ] = None,
    min_days: Annotated[
        int | None, Query(ge=0, description="At least this many days in stock (included).")
    ] = None,
    max_days: Annotated[
        int | None, Query(ge=0, description="At most this many days in stock (included).")
    ] = None,
    status: Annotated[StockStatus | None, Query(description="Only this stock status.")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Page size.")] = 50,
    offset: Annotated[int, Query(ge=0, description="How many vehicles to skip.")] = 0,
) -> VehiclePage:
    if min_days is not None and max_days is not None and min_days > max_days:
        raise ApiError(
            422,
            "invalid_input",
            f"min_days ({min_days}) is larger than max_days ({max_days}). "
            "Swap them or remove one.",
            [{"field": "min_days", "problem": "must not be larger than max_days"}],
        )
    filters = VehicleFilters(dealership_id, make, model, min_days, max_days, status)
    views, total = list_vehicles(session, filters, reference_date, limit, offset)
    return VehiclePage(
        items=[to_vehicle_out(v) for v in views], total=total, limit=limit, offset=offset
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleOut,
    summary="Get one vehicle",
    responses=error_responses(404, 422),
)
def get_vehicle_route(
    vehicle_id: int,
    session: Annotated[Session, Depends(get_session)],
    reference_date: Annotated[date, Depends(get_reference_date)],
) -> VehicleOut:
    view = get_vehicle(session, vehicle_id, reference_date)
    if view is None:
        raise vehicle_not_found(vehicle_id)
    return to_vehicle_out(view)


def vehicle_not_found(vehicle_id: int) -> ApiError:
    return ApiError(
        404,
        "vehicle_not_found",
        f"There is no vehicle with ID {vehicle_id}. Check the ID in the vehicle list.",
    )
