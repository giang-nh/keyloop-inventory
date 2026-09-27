"""Checks that the project is wired up. Replaced by real tests as features arrive."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_app_starts_and_serves_its_api_contract():
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Intelligent Inventory Dashboard API"
