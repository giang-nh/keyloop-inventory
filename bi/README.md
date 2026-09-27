# Power BI dashboard

A demo view on top of the API's CSV exports (ADR 0006). It is a Power BI Project
(`.pbip`): the model and the report are text files.

| Folder | What it holds |
|---|---|
| `Inventory.SemanticModel/` | The data model: tables, relationships and DAX measures, in TMDL text files |
| `Inventory.Report/` | The four report pages, in PBIR (JSON) files |
| `theme.json` | The report theme (a copy is registered inside the report) |
| `data/` | The two CSV files the model reads. Not in Git: download them as below |

## 1. Get the data

Start the API with data loaded (see the main README, steps 3 and 4). Then, from the project
folder:

```bash
curl --create-dirs -o bi/data/vehicles.csv http://127.0.0.1:8000/api/v1/exports/vehicles.csv
```

```bash
curl --create-dirs -o bi/data/actions.csv http://127.0.0.1:8000/api/v1/exports/actions.csv
```

In Windows PowerShell 5.1, type `curl.exe` instead of `curl`.

## 2. Open the dashboard

1. Open `bi/Inventory.pbip` in Power BI Desktop.
2. **Transform data > Edit parameters**: set `CsvFolder` to the full path of your `bi/data`
   folder, for example `D:\keyloop-inventory\bi\data`.
3. **Refresh**.

## The pages

| Page | The manager's question |
|---|---|
| Stock overview | What do I have in stock, and where are the problem cars? |
| Aging list | Which cars are over 90 days, and what has been decided about them? |
| Action effect | Do cars with an action sell, and how fast? |
| Monthly sales | How many cars sell each month, and how long did they sit first? |

Every page has filters for dealership, make and model.

## Rules the model follows

- **The dashboard never works out aging.** `Days In Stock` and `Stock Status` come from the
  API. Measures only count, sum and average them (SPEC R4).
- **The latest action** uses the API's rule (ADR 0004): newest time first, the higher action
  ID wins a tie.
- Every table, column and measure has a description (the `///` lines in the `.tmdl` files).
