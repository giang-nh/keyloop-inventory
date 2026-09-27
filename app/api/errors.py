"""One error shape for every error response (SYSTEM_DESIGN 5.6).

    {"error": {"code": "...", "message": "...", "details": [...]}}

`code` is for programs. `message` is for people: it says what went wrong and what to do.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """An error the client can act on."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def error_body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def _api_error(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        error_body(exc.code, exc.message, exc.details), status_code=exc.status_code
    )


def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            # Drop the first part ("query", "body", "path"): clients care about the field.
            "field": ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]),
            "problem": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body(
            "invalid_input",
            "Some of the input is not valid. See details for each field, fix it and try again.",
            details,
        ),
    )


def _http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    message = "This address does not exist." if exc.status_code == 404 else str(exc.detail)
    return JSONResponse(
        error_body(code, message), status_code=exc.status_code, headers=exc.headers
    )


def add_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
