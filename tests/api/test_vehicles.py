"""The vehicle list (R1) and the summary (R2). Test names include the criterion they prove."""

from sqlalchemy import select

from app.models import Dealership, Vehicle
from app.services.inventory import LIST_ORDER

LIST = "/api/v1/vehicles"


def vins(response):
    return [item["vin"] for item in response.json()["items"]]


def test_ac_1_1_list_shows_only_vehicles_in_stock(client, add_vehicle):
    add_vehicle(vin="INSTOCK0000000001")
    add_vehicle(vin="SOLD0000000000001", days=50, sold_days_ago=5)

    response = client.get(LIST)

    assert response.status_code == 200
    assert vins(response) == ["INSTOCK0000000001"]


def test_ac_1_2_each_vehicle_shows_the_required_fields(client, seeded):
    item = client.get(LIST, params={"make": "Mitsubishi"}).json()["items"][0]

    assert item["id"] > 0
    assert item["vin"] == "SEED0000000000009"
    assert item["dealership_name"] == "Harbour Auto"
    assert (item["make"], item["model"], item["model_year"]) == ("Mitsubishi", "Xpander", 2023)
    assert item["price"] == 560_000_000
    assert item["stock_in_date"] == "2024-12-11"
    assert item["days_in_stock"] == 400
    assert item["stock_status"] == "aging"
    assert item["latest_action"]["action_type"] == "SEND_TO_AUCTION"


def test_ac_1_2_vehicle_without_actions_has_no_latest_action(client, add_vehicle):
    add_vehicle()

    assert client.get(LIST).json()["items"][0]["latest_action"] is None


def test_ac_1_3_filter_by_dealership(client, seeded):
    riverside = seeded.scalar(select(Dealership).where(Dealership.name == "Riverside Motors"))

    items = client.get(LIST, params={"dealership_id": riverside.id}).json()["items"]

    assert items
    assert {i["dealership_name"] for i in items} == {"Riverside Motors"}


def test_ac_1_4_filter_by_make_is_exact_and_ignores_case(client, seeded):
    assert {i["make"] for i in client.get(LIST, params={"make": "toyota"}).json()["items"]} == {
        "Toyota"
    }
    assert client.get(LIST, params={"make": "Toy"}).json()["total"] == 0


def test_ac_1_5_filter_by_model_is_exact_and_ignores_case(client, seeded):
    items = client.get(LIST, params={"model": "CX-5"}).json()["items"]
    assert [i["model"] for i in items] == ["CX-5"]
    assert client.get(LIST, params={"model": "cx-5"}).json()["total"] == 1
    assert client.get(LIST, params={"model": "CX"}).json()["total"] == 0


def test_ac_1_6_filter_by_days_in_stock_includes_both_limits(client, seeded):
    days = [
        i["days_in_stock"]
        for i in client.get(LIST, params={"min_days": 76, "max_days": 90}).json()["items"]
    ]

    assert sorted(days) == [76, 89, 90]


def test_ac_1_7_filter_by_stock_status(client, seeded):
    def statuses(status):
        items = client.get(LIST, params={"status": status}).json()["items"]
        return sorted(i["days_in_stock"] for i in items if i["days_in_stock"] is not None), [
            i["stock_status"] for i in items
        ]

    aging_days, aging_labels = statuses("aging")
    assert aging_days == [91, 95, 120, 400]
    assert set(aging_labels) == {"aging"}

    approaching_days, _ = statuses("approaching")
    assert approaching_days == [76, 89, 90]

    fresh_days, _ = statuses("fresh")
    assert fresh_days == [0, 30, 75]

    unknown = client.get(LIST, params={"status": "unknown"}).json()["items"]
    assert [i["vin"] for i in unknown] == ["SEED0000000000010"]


def test_ac_1_8_filters_combine_so_all_must_match(client, seeded):
    items = client.get(LIST, params={"make": "Ford", "status": "aging", "max_days": 100}).json()[
        "items"
    ]

    assert [(i["model"], i["days_in_stock"]) for i in items] == [("Ranger", 91)]


def test_ac_1_9_no_stock_in_date_first_then_oldest_first(client, seeded):
    days = [i["days_in_stock"] for i in client.get(LIST).json()["items"]]

    assert days[0] is None
    assert days[1:] == sorted(days[1:], reverse=True)


def test_ac_1_9_ties_are_ordered_by_id_so_pages_never_repeat_or_skip(client, add_vehicle):
    created = [add_vehicle(days=100, vin=f"SAMEDAY{n:010d}") for n in range(7)]

    seen = []
    for offset in range(0, 7, 3):
        seen += [i["id"] for i in client.get(LIST, params={"limit": 3, "offset": offset}).json()[
            "items"
        ]]

    assert seen == [v.id for v in created]


def test_ac_1_9_order_always_ends_with_the_vehicle_id():
    """SQLite happens to return ties in ID order, so the paging test above would pass even
    without the ID tie-break. PostgreSQL does not promise that. This checks the rule itself."""
    last = LIST_ORDER[-1]

    assert last.element.compare(Vehicle.__table__.c.id)
    assert last.modifier.__name__ == "asc_op"


def test_ac_1_10_list_is_paged_with_a_total(client, add_vehicle):
    for n in range(60):
        add_vehicle(days=n, vin=f"PAGE{n:013d}")

    first = client.get(LIST).json()
    assert (len(first["items"]), first["total"], first["limit"], first["offset"]) == (50, 60, 50, 0)

    second = client.get(LIST, params={"offset": 50}).json()
    assert len(second["items"]) == 10

    assert client.get(LIST, params={"limit": 200}).status_code == 200
    assert client.get(LIST, params={"limit": 201}).status_code == 422


def test_ac_1_11_invalid_filters_return_422_with_a_clear_message(client):
    for params, field in [
        ({"min_days": -1}, "min_days"),
        ({"limit": 201}, "limit"),
        ({"status": "old"}, "status"),
        ({"min_days": 50, "max_days": 10}, "min_days"),
    ]:
        response = client.get(LIST, params=params)
        body = response.json()["error"]
        assert response.status_code == 422, params
        assert body["code"] == "invalid_input"
        assert body["message"]
        assert body["details"][0]["field"] == field


def test_ac_2_7_sold_vehicles_have_no_stock_status(client, add_vehicle):
    sold = add_vehicle(days=200, sold_days_ago=1)

    body = client.get(f"{LIST}/{sold.id}").json()

    assert body["sold_date"] is not None
    assert body["stock_status"] is None
    assert body["days_in_stock"] is None


def test_get_one_vehicle_and_unknown_id(client, seeded):
    first_id = client.get(LIST).json()["items"][0]["id"]

    assert client.get(f"{LIST}/{first_id}").json()["id"] == first_id

    missing = client.get(f"{LIST}/999999")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "vehicle_not_found"


def test_ac_2_8_summary_counts_and_values_for_all_dealerships(client, seeded):
    body = client.get("/api/v1/inventory/summary").json()

    assert body == {
        "dealership_id": None,
        # 13 seed records minus 2 sold (the Vios, and the first stay of the trade-in).
        "vehicles_in_stock": 11,
        "aging_count": 4,  # 91, 95, 120, 400 days
        "approaching_count": 3,  # 76, 89, 90 days
        "aging_value": 707_000_000 + 320_000_000 + 1_099_000_000 + 560_000_000,
        "approaching_value": 599_000_000 + 1_055_000_000 + 749_000_000,
    }


def test_ac_2_8_summary_for_one_dealership(client, seeded):
    lakeside = seeded.scalar(select(Dealership).where(Dealership.name == "Lakeside Cars"))

    body = client.get("/api/v1/inventory/summary", params={"dealership_id": lakeside.id}).json()

    assert (body["aging_count"], body["approaching_count"], body["vehicles_in_stock"]) == (1, 1, 3)
    assert client.get("/api/v1/inventory/summary", params={"dealership_id": 999}).status_code == 404


def test_dealership_list(client, seeded):
    names = [d["name"] for d in client.get("/api/v1/dealerships").json()]

    assert names == ["Harbour Auto", "Lakeside Cars", "Riverside Motors"]
