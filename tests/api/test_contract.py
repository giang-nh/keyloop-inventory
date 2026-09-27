"""The committed API contract must match the code, and describe real error bodies."""

import json
import sys
from pathlib import Path

from app.api.schemas import ErrorResponse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from export_openapi import OUTPUT, contract  # noqa: E402


def test_committed_contract_matches_the_code():
    committed = OUTPUT.read_text(encoding="utf-8")

    assert json.loads(committed) == json.loads(contract()), (
        "docs/api/openapi.json is out of date. Run: python scripts/export_openapi.py"
    )


def test_contract_documents_errors_with_the_real_error_shape():
    spec = json.loads(contract())

    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            for status in ("404", "422"):
                if status in operation["responses"]:
                    schema = operation["responses"][status]["content"]["application/json"]
                    assert schema["schema"]["$ref"].endswith("/ErrorResponse"), (method, path)
    assert "HTTPValidationError" not in json.dumps(spec)


def test_real_error_bodies_match_the_documented_shape(client, add_vehicle):
    fresh = add_vehicle(days=5)
    bodies = [
        client.get("/api/v1/vehicles/999").json(),
        client.get("/api/v1/vehicles", params={"limit": 0}).json(),
        client.post(f"/api/v1/vehicles/{fresh.id}/actions",
                    json={"action_type": "OTHER", "created_by": "A"}).json(),
        client.get("/no/such/path").json(),
    ]

    for body in bodies:
        ErrorResponse.model_validate(body)
