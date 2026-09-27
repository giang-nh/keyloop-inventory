"""Inventory-wide routes: the summary and the list of dealerships."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_reference_date, get_session
from app.api.errors import ApiError
from app.api.schemas import DealershipOut, InventorySummary, error_responses
from app.models import Dealership
from app.services.inventory import summary

router = APIRouter(prefix="/api/v1", tags=["Inventory"])


@router.get(
    "/inventory/summary",
    response_model=InventorySummary,
    summary="How much stock is aging or about to be",
    description="Counts and total list price of aging and approaching vehicles in stock.",
    responses=error_responses(404, 422),
)
def summary_route(
    session: Annotated[Session, Depends(get_session)],
    reference_date: Annotated[date, Depends(get_reference_date)],
    dealership_id: Annotated[
        int | None, Query(ge=1, description="One dealership. Leave out for all dealerships.")
    ] = None,
) -> InventorySummary:
    if dealership_id is not None and session.get(Dealership, dealership_id) is None:
        raise ApiError(
            404,
            "dealership_not_found",
            f"There is no dealership with ID {dealership_id}. "
            "See /api/v1/dealerships for the list.",
        )
    return InventorySummary(**summary(session, reference_date, dealership_id))


@router.get(
    "/dealerships",
    response_model=list[DealershipOut],
    summary="List dealerships",
    description="Use these IDs for the dealership filter.",
)
def dealerships_route(session: Annotated[Session, Depends(get_session)]) -> list[Dealership]:
    return list(session.scalars(select(Dealership).order_by(Dealership.name)))
