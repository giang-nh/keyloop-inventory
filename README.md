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

## Checks before every push

Lint and the full test suite run automatically before every `git push`, through a Git
hook stored in the repository. Turn it on once per clone:

```bash
git config core.hooksPath .githooks
```

A GitHub Actions workflow with the same checks is in `.github/workflows/ci.yml`.
GitHub-hosted runners were not available on this account, so it is set to run only when
started by hand, and the checks run locally through the hook instead.

