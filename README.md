# Intelligent Inventory Dashboard

A backend service that helps dealership managers see their vehicle stock, find vehicles
that have been in stock for more than 90 days, and record what to do about them.

> Work in progress. Full build, run and test instructions come with issue #21.
> Start with [`docs/SPEC.md`](docs/SPEC.md) for what the service does and why.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
```
