"""CSV export routes for reporting tools (SPEC R4)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_reference_date
from app.services.exports import (
    ACTION_COLUMNS,
    VEHICLE_COLUMNS,
    actions_csv,
    columns_description,
    vehicles_csv,
)

router = APIRouter(prefix="/api/v1/exports", tags=["Exports"])

_CSV = {200: {"content": {"text/csv": {}}, "description": "A CSV file with a header row."}}


def _csv_response(chunks, filename: str) -> StreamingResponse:
    return StreamingResponse(
        chunks,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/vehicles.csv",
    summary="All vehicles as CSV",
    description=(
        "Every vehicle, in stock and sold, for Power BI or Excel (Get Data > Web). "
        "Days in stock and status use the same rule as the API.\n\nColumns:\n\n"
        + columns_description(VEHICLE_COLUMNS)
    ),
    response_class=StreamingResponse,
    responses=_CSV,
)
def vehicles_export(
    request: Request, reference_date: Annotated[date, Depends(get_reference_date)]
) -> StreamingResponse:
    return _csv_response(
        vehicles_csv(request.app.state.session_factory, reference_date), "vehicles.csv"
    )


@router.get(
    "/actions.csv",
    summary="All actions as CSV",
    description=(
        "Every recorded action, for Power BI or Excel.\n\nColumns:\n\n"
        + columns_description(ACTION_COLUMNS)
    ),
    response_class=StreamingResponse,
    responses=_CSV,
)
def actions_export(request: Request) -> StreamingResponse:
    return _csv_response(actions_csv(request.app.state.session_factory), "actions.csv")
