# API examples with cURL

These examples stand in for the manager's screen, which is not part of this assessment.
Every command below was run against a local server loaded with the seed data, and the
responses shown are real (last run 2026-09-27, after the switch to VND) (shortened where marked with `…`).

The full contract is in [`openapi.json`](openapi.json). With the server running, the same
contract is shown as an interactive page at <http://localhost:8000/docs>.

## Start a local server

```bash
alembic upgrade head          # create the tables
python scripts/seed.py        # load the small seed dataset
uvicorn app.main:app          # serve on http://localhost:8000
```

Seed dates are set relative to the day you run it, so dates in your responses will differ
from the ones below. Days in stock and statuses will match.

---

## 1. See the dealerships

```bash
curl -s "http://localhost:8000/api/v1/dealerships"
```

```json
[
  {"id": 2, "name": "Harbour Auto", "city": "Da Nang"},
  {"id": 3, "name": "Lakeside Cars", "city": "Hanoi"},
  {"id": 1, "name": "Riverside Motors", "city": "Ho Chi Minh City"}
]
```

## 2. List aging vehicles, oldest first

```bash
curl -s "http://localhost:8000/api/v1/vehicles?status=aging&limit=2"
```

```json
{
  "items": [
    {
      "id": 9, "vin": "SEED0000000000009",
      "dealership_id": 2, "dealership_name": "Harbour Auto",
      "make": "Mitsubishi", "model": "Xpander", "model_year": 2023, "price": 560000000,
      "stock_in_date": "2025-08-23", "sold_date": null,
      "days_in_stock": 400, "stock_status": "aging",
      "latest_action": {"id": 3, "action_type": "SEND_TO_AUCTION", "created_by": "Minh Pham", …}
    },
    …
  ],
  "total": 4, "limit": 2, "offset": 0
}
```

## 3. Combine filters

Make and model are exact matches that ignore case. All filters must match.

```bash
curl -s "http://localhost:8000/api/v1/vehicles?make=toyota&min_days=60"
```

```json
{
  "items": [
    {"id": 5, "make": "Toyota", "model": "Fortuner", "days_in_stock": 89,
     "stock_status": "approaching", …}
  ],
  "total": 1, "limit": 50, "offset": 0
}
```

## 4. A filter that does not make sense

```bash
curl -s "http://localhost:8000/api/v1/vehicles?min_days=50&max_days=10"
```

```json
{
  "error": {
    "code": "invalid_input",
    "message": "min_days (50) is larger than max_days (10). Swap them or remove one.",
    "details": [{"field": "min_days", "problem": "must not be larger than max_days"}]
  }
}
```

## 5. How much money is tied up

```bash
curl -s "http://localhost:8000/api/v1/inventory/summary"
```

```json
{
  "dealership_id": null,
  "vehicles_in_stock": 11,
  "aging_count": 4,
  "approaching_count": 3,
  "aging_value": 2686000000,
  "approaching_value": 2403000000
}
```

Values are list prices in VND. Add `?dealership_id=1` for one dealership.

## 6. Record an action for an aging vehicle

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/8/actions" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "PRICE_REDUCTION_PLANNED", "created_by": "Linh Tran", "note": "Reduce by 5%"}'
```

Response `201 Created`. The service sets the time:

```json
{
  "id": 6, "vehicle_id": 8, "action_type": "PRICE_REDUCTION_PLANNED",
  "note": "Reduce by 5%", "created_by": "Linh Tran",
  "created_at": "2026-09-27T12:28:20.053434Z"
}
```

## 7. An action that is not allowed

Vehicle 2 has been in stock for 30 days, so it is `fresh`:

```bash
curl -s -X POST "http://localhost:8000/api/v1/vehicles/2/actions" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "OTHER", "created_by": "Linh Tran"}'
```

Response `422`:

```json
{
  "error": {
    "code": "vehicle_not_eligible",
    "message": "Vehicle 2 has been in stock for 30 days. Actions can only be recorded for vehicles in stock for 76 days or more.",
    "details": []
  }
}
```

## 8. A vehicle's history, newest first

```bash
curl -s "http://localhost:8000/api/v1/vehicles/8/actions"
```

```json
[
  {"id": 6, "action_type": "PRICE_REDUCTION_PLANNED", "note": "Reduce by 5%", …},
  {"id": 4, "action_type": "MARKETING_PROMOTION", "note": "Feature in weekend campaign", …}
]
```

## 9. Export for Power BI or Excel

```bash
curl -s "http://localhost:8000/api/v1/exports/vehicles.csv" | head -3
```

```csv
vehicle_id,vin,dealership_id,dealership_name,make,model,model_year,price,stock_in_date,sold_date,in_stock,days_in_stock,stock_status
1,SEED0000000000001,1,Riverside Motors,Toyota,Corolla Cross,2025,820000000,2026-09-27,,true,0,fresh
2,SEED0000000000002,1,Riverside Motors,Honda,CR-V,2025,1029000000,2026-08-28,,true,30,fresh
```

The file starts with a byte order mark, so Excel shows Vietnamese accents correctly.
The actions export is at `/api/v1/exports/actions.csv`.

## 10. Operations

Follow one request through the logs with your own request ID:

```bash
curl -s -i "http://localhost:8000/health" -H "X-Request-ID: demo-123"
```

```
HTTP/1.1 200 OK
x-request-id: demo-123

{"status":"ok","database":"ok","schema":"up_to_date"}
```

The matching log line on the server:

```json
{"time": "2026-09-27T11:35:38.132+00:00", "level": "INFO", "event": "request",
 "request_id": "demo-123", "method": "GET", "path": "/health", "route": "/health",
 "status": 200, "duration_ms": 1.7}
```

Metrics for a monitoring tool:

```bash
curl -s "http://localhost:8000/metrics" | grep vehicle_actions_recorded_total
```

```
vehicle_actions_recorded_total{action_type="PRICE_REDUCTION_PLANNED"} 1.0
```
