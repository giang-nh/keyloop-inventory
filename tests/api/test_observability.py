"""Health, metrics, request IDs and logs (SYSTEM_DESIGN section 7)."""

import json
import logging

import pytest

from app.observability import JsonFormatter
from tests.api.conftest import make_client


@pytest.fixture
def log_lines():
    """Collect the service's log lines, formatted as they are in production."""
    lines = []

    class Collect(logging.Handler):
        def emit(self, record):
            lines.append(json.loads(self.format(record)))

    handler = Collect()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("inventory")
    logger.addHandler(handler)
    yield lines
    logger.removeHandler(handler)


def test_health_is_ok_when_the_database_is_reachable(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_is_503_when_the_database_is_unreachable(tmp_path):
    missing_folder = tmp_path / "does-not-exist" / "db.sqlite"
    with make_client(f"sqlite:///{missing_folder.as_posix()}") as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_every_response_has_a_request_id(client):
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]

    assert first and second and first != second


def test_a_safe_incoming_request_id_is_kept(client):
    response = client.get("/health", headers={"X-Request-ID": "abc-123_XYZ"})

    assert response.headers["X-Request-ID"] == "abc-123_XYZ"


@pytest.mark.parametrize("unsafe", ["x" * 65, "has spaces", "semi;colon", "quote\"d", ""])
def test_an_unsafe_incoming_request_id_is_replaced(client, unsafe):
    response = client.get("/health", headers={"X-Request-ID": unsafe})

    returned = response.headers["X-Request-ID"]
    assert returned != unsafe
    assert len(returned) == 32


def test_each_request_writes_one_json_log_line_with_its_request_id(client, log_lines):
    client.get("/api/v1/vehicles", headers={"X-Request-ID": "trace-me"})

    requests = [line for line in log_lines if line["event"] == "request"]
    assert len(requests) == 1
    line = requests[0]
    assert line["request_id"] == "trace-me"
    assert (line["method"], line["route"], line["status"]) == ("GET", "/api/v1/vehicles", 200)
    assert isinstance(line["duration_ms"], float)
    assert line["time"].endswith("+00:00")


def test_notes_and_names_are_never_written_to_the_logs(client, add_vehicle, log_lines):
    vehicle = add_vehicle(days=120)
    secret_note = "Customer Jane Doe, phone 555-0142"

    client.post(
        f"/api/v1/vehicles/{vehicle.id}/actions",
        json={"action_type": "OTHER", "created_by": "Manager Name", "note": secret_note},
        headers={"X-Request-ID": "action-1"},
    )

    everything_logged = json.dumps(log_lines)
    assert "Jane Doe" not in everything_logged
    assert "555-0142" not in everything_logged
    assert "Manager Name" not in everything_logged

    recorded = [line for line in log_lines if line["event"] == "action_recorded"]
    assert recorded[0]["vehicle_id"] == vehicle.id
    assert recorded[0]["request_id"] == "action-1"


def test_metrics_use_the_route_pattern_not_the_real_path(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    client.get(f"/api/v1/vehicles/{vehicle.id}")
    client.get("/api/v1/vehicles/999999")

    text = client.get("/metrics").text

    assert 'route="/api/v1/vehicles/{vehicle_id}"' in text
    assert 'status="200"' in text and 'status="404"' in text
    assert f"/api/v1/vehicles/{vehicle.id}\"" not in text
    assert "http_request_duration_seconds_bucket" in text


def test_metrics_count_recorded_actions_by_type(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    for _ in range(2):
        client.post(
            f"/api/v1/vehicles/{vehicle.id}/actions",
            json={"action_type": "SEND_TO_AUCTION", "created_by": "A"},
        )

    text = client.get("/metrics").text

    assert 'vehicle_actions_recorded_total{action_type="SEND_TO_AUCTION"} 2.0' in text
