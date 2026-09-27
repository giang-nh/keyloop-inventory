"""Recording and reading actions (R3). Test names include the criterion they prove."""

from datetime import timedelta

from app.api.deps import get_now
from tests.api.conftest import NOW, make_client


def actions_url(vehicle_id: int) -> str:
    return f"/api/v1/vehicles/{vehicle_id}/actions"


def body(**changes):
    data = {"action_type": "PRICE_REDUCTION_PLANNED", "created_by": "Linh Tran", "note": "5% off"}
    data.update(changes)
    return data


def test_ac_3_1_record_an_action_for_an_aging_vehicle(client, add_vehicle):
    vehicle = add_vehicle(days=91)

    response = client.post(actions_url(vehicle.id), json=body())

    assert response.status_code == 201
    saved = response.json()
    assert saved["vehicle_id"] == vehicle.id
    assert saved["action_type"] == "PRICE_REDUCTION_PLANNED"
    assert saved["created_by"] == "Linh Tran"
    assert saved["note"] == "5% off"
    assert saved["created_at"] == "2026-01-15T10:30:00Z"


def test_ac_3_1_record_an_action_for_an_approaching_vehicle(client, add_vehicle):
    vehicle = add_vehicle(days=76)

    assert client.post(actions_url(vehicle.id), json=body()).status_code == 201


def test_ac_3_1_note_is_optional(client, add_vehicle):
    vehicle = add_vehicle(days=120)

    response = client.post(actions_url(vehicle.id), json=body(note=None))

    assert response.status_code == 201
    assert response.json()["note"] is None


def test_ac_3_1_name_and_note_limits(client, add_vehicle):
    vehicle = add_vehicle(days=120)

    assert client.post(actions_url(vehicle.id), json=body(note="x" * 500)).status_code == 201
    assert client.post(actions_url(vehicle.id), json=body(note="x" * 501)).status_code == 422
    assert client.post(actions_url(vehicle.id), json=body(created_by="x" * 100)).status_code == 201
    assert client.post(actions_url(vehicle.id), json=body(created_by="x" * 101)).status_code == 422
    assert client.post(actions_url(vehicle.id), json=body(created_by="   ")).status_code == 422


def test_ac_3_1_client_cannot_set_the_time(client, add_vehicle):
    vehicle = add_vehicle(days=120)

    response = client.post(actions_url(vehicle.id), json=body(created_at="2020-01-01T00:00:00Z"))

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "created_at"


def test_ac_3_2_unknown_action_type_is_rejected(client, add_vehicle):
    vehicle = add_vehicle(days=120)

    response = client.post(actions_url(vehicle.id), json=body(action_type="SELL_TO_STAFF"))

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "action_type"


def test_ac_3_2_every_listed_action_type_is_accepted(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    types = [
        "PRICE_REDUCTION_PLANNED",
        "MARKETING_PROMOTION",
        "TRANSFER_TO_ANOTHER_DEALERSHIP",
        "SEND_TO_AUCTION",
        "UNDER_REVIEW",
        "OTHER",
    ]

    for action_type in types:
        response = client.post(actions_url(vehicle.id), json=body(action_type=action_type))
        assert response.status_code == 201, action_type


def test_ac_3_3_fresh_vehicle_cannot_get_an_action(client, add_vehicle):
    vehicle = add_vehicle(days=75)

    response = client.post(actions_url(vehicle.id), json=body())

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "vehicle_not_eligible"
    assert "75 days" in error["message"] and "76 days or more" in error["message"]


def test_ac_3_3_vehicle_with_unknown_date_cannot_get_an_action(client, add_vehicle):
    vehicle = add_vehicle(days=None)

    response = client.post(actions_url(vehicle.id), json=body())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "vehicle_stock_in_date_unknown"


def test_ac_3_3_sold_vehicle_cannot_get_an_action(client, add_vehicle):
    vehicle = add_vehicle(days=200, sold_days_ago=3)

    response = client.post(actions_url(vehicle.id), json=body())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "vehicle_sold"


def test_ac_3_4_unknown_vehicle_returns_404(client):
    assert client.post(actions_url(999), json=body()).status_code == 404
    response = client.get(actions_url(999))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "vehicle_not_found"


def test_ac_3_5_history_is_newest_first(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    for hours, action_type in [(0, "UNDER_REVIEW"), (1, "PRICE_REDUCTION_PLANNED"),
                               (2, "SEND_TO_AUCTION")]:
        client.app.dependency_overrides[get_now] = lambda h=hours: NOW + timedelta(hours=h)
        client.post(actions_url(vehicle.id), json=body(action_type=action_type))

    history = client.get(actions_url(vehicle.id)).json()

    assert [a["action_type"] for a in history] == [
        "SEND_TO_AUCTION",
        "PRICE_REDUCTION_PLANNED",
        "UNDER_REVIEW",
    ]


def test_ac_3_5_same_time_actions_keep_the_order_they_were_saved(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    client.post(actions_url(vehicle.id), json=body(action_type="UNDER_REVIEW"))
    client.post(actions_url(vehicle.id), json=body(action_type="OTHER"))

    history = client.get(actions_url(vehicle.id)).json()
    latest = client.get(f"/api/v1/vehicles/{vehicle.id}").json()["latest_action"]

    assert [a["action_type"] for a in history] == ["OTHER", "UNDER_REVIEW"]
    assert latest["action_type"] == "OTHER"


def test_ac_3_6_actions_cannot_be_changed_or_deleted(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    first = client.post(actions_url(vehicle.id), json=body(note="first")).json()
    client.post(actions_url(vehicle.id), json=body(note="second"))

    for method in ("put", "patch", "delete"):
        response = client.request(method, f"{actions_url(vehicle.id)}/{first['id']}")
        assert response.status_code in (404, 405), method

    history = client.get(actions_url(vehicle.id)).json()
    assert [a["note"] for a in history] == ["second", "first"]
    assert history[1] == first


def test_ac_3_7_actions_survive_a_restart(engine, database_url, add_vehicle):
    vehicle = add_vehicle(days=120)
    with make_client(database_url) as before_restart:
        saved = before_restart.post(actions_url(vehicle.id), json=body()).json()

    with make_client(database_url) as after_restart:
        history = after_restart.get(actions_url(vehicle.id)).json()

    assert history == [saved]
