# ADR 0006: Power BI as a demo view on top of the CSV exports

**Status:** Accepted · 2026-09-27

## Context

The manager's fourth question is "is it getting better or worse?" (SPEC Step 4). A
reporting tool draws charts better than an API does. The challenge grades one layer only,
the backend, so any dashboard is a demo view, not a product screen.

## Decision

- **Power BI reads the two CSV exports** (`vehicles.csv`, `actions.csv`) from a folder on
  disk. The files are downloaded from `GET /api/v1/exports/*.csv`. The folder path is one
  parameter, `CsvFolder`.
- **Power BI never works out aging.** Days in stock and stock status come from the CSV as the
  API sent them (SPEC R4). The dashboard only counts, sums and averages them.
- **No aging trend over time.** It would need each car's status on each past date, which the
  exports do not carry. Working it out in DAX (Power BI's formula language) would copy the
  aging rule into a second place, so it is left out (owner's decision, issue #27).
- **Saved as a Power BI Project (`.pbip`)**: the model and report are text files that can be
  reviewed in Git, not a binary `.pbix`.

## Why

- **One rule, one place.** If the aging threshold changes, only the API changes. The
  dashboard cannot drift.
- **Works without a running API.** Reading files lets the demo run offline, and the files can
  be opened in Excel to check any number on the dashboard.
- **Reviewable.** Every measure has a plain-English description in the `.tmdl` files.

## Considered

- **Power BI reads the API over HTTP (Get Data > Web).** Always fresh, but the API must be
  running for every refresh. Chosen against for the demo; switching is a one-line change in
  each table's source.
- **Power BI reads the SQLite database directly.** Needs an ODBC driver, and the dashboard
  would have to copy the aging rule. Rejected.
- **Aging trend worked out in DAX.** Rejected, see above. If the trend is needed, the next
  step is a history export built by the backend with the same rule.

## Consequences

- The data is only as fresh as the last download. The dashboard shows cars "as of" the day
  the files were exported (SPEC D-14).
- The action-effect page compares cars with and without actions. Managers act on cars that
  are already hard to sell, so this shows what happened, not what caused it. The page says so.
