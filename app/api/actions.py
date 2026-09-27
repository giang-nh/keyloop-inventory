"""Action routes: record an action for a vehicle, and read its history."""

import logging
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_now, get_reference_date, get_session
from app.api.errors import ApiError
from app.api.schemas import ActionIn, ActionOut, error_responses
from app.api.vehicles import vehicle_not_found
from app.services.actions import (
    ActionNotAllowedError,
    VehicleNotFoundError,
    list_actions,
    record_action,
)

logger = logging.getLogger("inventory")

router = APIRouter(prefix="/api/v1/vehicles/{vehicle_id}/actions", tags=["Actions"])


@router.post(
    "",
    response_model=ActionOut,
    status_code=201,
    summary="Record an action for a vehicle",
    description=(
        "Record a status or planned action for a vehicle that is aging or approaching aging. "
        "Actions cannot be changed or deleted later. The service sets the time."
    ),
    responses=error_responses(404, 422),
)
def record_action_route(
    vehicle_id: int,
    body: ActionIn,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    reference_date: Annotated[date, Depends(get_reference_date)],
    now: Annotated[datetime, Depends(get_now)],
) -> ActionOut:
    try:
        action = record_action(
            session, vehicle_id, body.action_type, body.created_by, body.note, reference_date, now
        )
    except VehicleNotFoundError:
        raise vehicle_not_found(vehicle_id) from None
    except ActionNotAllowedError as error:
        raise ApiError(422, error.code, str(error)) from None

    request.app.state.metrics.actions_recorded.labels(action.action_type.value).inc()
    # IDs and type only: the note and the manager's name stay out of the logs.
    logger.info(
        "action_recorded",
        extra={
            "fields": {
                "vehicle_id": vehicle_id,
                "action_id": action.id,
                "action_type": action.action_type.value,
            }
        },
    )
    return ActionOut.model_validate(action)


@router.get(
    "",
    response_model=list[ActionOut],
    summary="A vehicle's action history",
    description="Every action recorded for the vehicle, newest first.",
    responses=error_responses(404, 422),
)
def list_actions_route(
    vehicle_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[ActionOut]:
    try:
        actions = list_actions(session, vehicle_id)
    except VehicleNotFoundError:
        raise vehicle_not_found(vehicle_id) from None
    return [ActionOut.model_validate(a) for a in actions]
