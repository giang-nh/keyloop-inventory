"""CSV exports for reporting tools (R4). Test names include the criterion they prove."""

import csv
import io
import re

from app.services.exports import ACTION_COLUMNS, VEHICLE_COLUMNS, safe_text

VEHICLES_CSV = "/api/v1/exports/vehicles.csv"
ACTIONS_CSV = "/api/v1/exports/actions.csv"


def read_csv(response) -> list[dict]:
    return list(csv.DictReader(io.StringIO(response.text)))


def test_ac_4_1_vehicles_csv_includes_in_stock_and_sold_vehicles(client, seeded):
    rows = read_csv(client.get(VEHICLES_CSV))

    assert len(rows) == 13
    assert {r["in_stock"] for r in rows} == {"true", "false"}
    assert sum(r["in_stock"] == "false" for r in rows) == 2


def test_ac_4_1_csv_status_matches_the_api_for_every_vehicle_in_stock(client, seeded):
    rows = {int(r["vehicle_id"]): r for r in read_csv(client.get(VEHICLES_CSV))}
    api_items = client.get("/api/v1/vehicles", params={"limit": 200}).json()["items"]

    assert api_items
    for item in api_items:
        row = rows[item["id"]]
        assert row["stock_status"] == item["stock_status"]
        assert row["days_in_stock"] == ("" if item["days_in_stock"] is None else
                                        str(item["days_in_stock"]))


def test_ac_4_1_sold_vehicles_have_days_to_sale_and_no_status(client, add_vehicle):
    add_vehicle(days=60, sold_days_ago=10)

    row = read_csv(client.get(VEHICLES_CSV))[0]

    assert row["days_in_stock"] == "50"
    assert row["stock_status"] == ""


def test_ac_4_2_actions_csv_includes_every_action(client, seeded):
    rows = read_csv(client.get(ACTIONS_CSV))

    assert len(rows) == 5
    assert {r["action_type"] for r in rows} >= {"SEND_TO_AUCTION", "UNDER_REVIEW"}


def test_ac_4_3_header_rows_match_the_documented_columns(client, seeded):
    vehicles = client.get(VEHICLES_CSV)
    actions = client.get(ACTIONS_CSV)

    assert vehicles.text.splitlines()[0].split(",") == [name for name, _ in VEHICLE_COLUMNS]
    assert actions.text.splitlines()[0].split(",") == [name for name, _ in ACTION_COLUMNS]
    assert vehicles.headers["content-type"].startswith("text/csv")
    assert 'filename="vehicles.csv"' in vehicles.headers["content-disposition"]


def test_ac_4_3_columns_are_listed_in_the_api_documentation(client):
    paths = client.get("/openapi.json").json()["paths"]

    vehicles_doc = paths[VEHICLES_CSV]["get"]["description"]
    actions_doc = paths[ACTIONS_CSV]["get"]["description"]
    assert all(f"`{name}`" in vehicles_doc for name, _ in VEHICLE_COLUMNS)
    assert all(f"`{name}`" in actions_doc for name, _ in ACTION_COLUMNS)


def test_ac_4_3_dates_use_iso_format(client, seeded):
    vehicles = read_csv(client.get(VEHICLES_CSV))
    actions = read_csv(client.get(ACTIONS_CSV))

    dates = [r["stock_in_date"] for r in vehicles if r["stock_in_date"]]
    dates += [r["sold_date"] for r in vehicles if r["sold_date"]]
    assert dates and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in dates)
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", r["created_at"])
               for r in actions)


def test_formula_like_text_is_made_safe_in_the_export(client, add_vehicle):
    vehicle = add_vehicle(days=120)
    for note in ['=HYPERLINK("http://example.com","Click")', "+1", "-2", "@SUM(A1)", "Plain"]:
        client.post(
            f"/api/v1/vehicles/{vehicle.id}/actions",
            json={"action_type": "OTHER", "created_by": "=cmd", "note": note},
        )

    notes = [r["note"] for r in read_csv(client.get(ACTIONS_CSV))]
    names = {r["created_by"] for r in read_csv(client.get(ACTIONS_CSV))}

    assert notes == ["'=HYPERLINK(\"http://example.com\",\"Click\")", "'+1", "'-2", "'@SUM(A1)",
                     "Plain"]
    assert names == {"'=cmd"}


def test_safe_text_leaves_normal_text_alone():
    assert safe_text("Toyota") == "Toyota"
    assert safe_text(None) == ""
    assert safe_text("a=b") == "a=b"


def test_large_exports_are_produced_in_chunks(engine, add_vehicle, monkeypatch):
    """Checked on the server side: the test client collects the whole response before
    handing it back, so it cannot show chunks."""
    import app.services.exports as exports
    from app.db import make_session_factory
    from tests.conftest import REFERENCE_DATE

    monkeypatch.setattr(exports, "BATCH_SIZE", 2)
    for n in range(5):
        add_vehicle(vin=f"CHUNK{n:012d}")

    chunks = list(exports.vehicles_csv(make_session_factory(engine), REFERENCE_DATE))

    assert len(chunks) == 3  # rows 1-2, rows 3-4, row 5 (the header rides with the first)
    assert len("".join(chunks).splitlines()) == 6  # header + 5 rows
