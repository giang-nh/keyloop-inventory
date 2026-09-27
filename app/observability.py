"""Logs, metrics and request IDs (SYSTEM_DESIGN section 7, ADR 0005).

- Every request gets a request ID. It is returned in the X-Request-ID header and written
  on every log line, so one request can be followed from start to end.
- Every request writes one JSON log line.
- Metrics are exposed at /metrics in the Prometheus format.

Free-text notes and managers' names are never logged (SYSTEM_DESIGN 5.6).
"""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

from app.api.errors import error_body
from app.db import current_schema_version, expected_schema_version

logger = logging.getLogger("inventory")

REQUEST_ID_HEADER = "X-Request-ID"
# Only short, plain IDs are trusted. Anything else could write fake lines into the logs.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def safe_request_id(incoming: str | None) -> str:
    """Use the caller's request ID if it is safe, otherwise make a new one."""
    if incoming and _SAFE_REQUEST_ID.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


class JsonFormatter(logging.Formatter):
    """One JSON object per line, with the request ID when there is one."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        request_id = _request_id.get()
        if request_id:
            entry["request_id"] = request_id
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry)


def configure_logging() -> None:
    """Send the service's logs to standard error as JSON. Safe to call more than once."""
    if any(isinstance(h.formatter, JsonFormatter) for h in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class Metrics:
    """The service's metrics. Each app has its own registry, so tests do not collide."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "http_requests_total",
            "HTTP requests, by method, route pattern and status code.",
            ["method", "route", "status"],
            registry=self.registry,
        )
        self.duration = Histogram(
            "http_request_duration_seconds",
            "How long requests take, by method and route pattern.",
            ["method", "route"],
            registry=self.registry,
        )
        self.actions_recorded = Counter(
            "vehicle_actions_recorded_total",
            "Actions recorded by managers, by action type.",
            ["action_type"],
            registry=self.registry,
        )


def _route_pattern(request: Request) -> str:
    # Label by pattern (/vehicles/{vehicle_id}), not the real path (/vehicles/42).
    # Otherwise every vehicle ID would become its own metric series.
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


def add_observability(app: FastAPI) -> None:
    configure_logging()
    metrics = Metrics()
    app.state.metrics = metrics

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = safe_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = _request_id.set(request_id)
        started = time.perf_counter()
        status = 500
        try:
            try:
                response = await call_next(request)
            except Exception:
                # Anything we did not expect. Log it with the request ID, and answer in the
                # usual error shape without internal details.
                logger.exception("unhandled_error")
                response = JSONResponse(
                    error_body(
                        "internal_error",
                        "Something went wrong on our side. Please try again. If it keeps "
                        f"happening, report request ID {request_id}.",
                    ),
                    status_code=500,
                )
            status = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            duration = time.perf_counter() - started
            route = _route_pattern(request)
            metrics.requests.labels(request.method, route, str(status)).inc()
            metrics.duration.labels(request.method, route).observe(duration)
            logger.info(
                "request",
                extra={
                    "fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "route": route,
                        "status": status,
                        "duration_ms": round(duration * 1000, 1),
                    }
                },
            )
            _request_id.reset(token)

    @app.get(
        "/health",
        tags=["Operations"],
        summary="Is the service up, can it reach the database, and is the database up to date?",
    )
    def health(request: Request) -> JSONResponse:
        # Reaching the database is not enough: a database without the tables (for example,
        # never migrated) would pass a simple connection check while every request fails.
        try:
            current = current_schema_version(request.app.state.engine)
        except Exception:
            logger.error("health_check_failed", extra={"fields": {"reason": "unreachable"}})
            body = {"status": "unavailable", "database": "unreachable"}
            return JSONResponse(body, status_code=503)
        expected = expected_schema_version()
        if current != expected:
            schema = "not_migrated" if current is None else "out_of_date"
            logger.error("health_check_failed", extra={"fields": {"reason": schema}})
            body = {"status": "unavailable", "database": "ok", "schema": schema,
                    "fix": "Run: alembic upgrade head"}
            return JSONResponse(body, status_code=503)
        return JSONResponse({"status": "ok", "database": "ok", "schema": "up_to_date"})

    @app.get("/metrics", tags=["Operations"], summary="Metrics for a monitoring tool")
    def metrics_endpoint() -> Response:
        return Response(generate_latest(metrics.registry), media_type=CONTENT_TYPE_LATEST)
