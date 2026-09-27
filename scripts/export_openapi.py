"""Write the API contract (OpenAPI) to docs/api/openapi.json.

Usage:
    python scripts/export_openapi.py

Run it after changing any route, so the committed contract matches the code.
A test fails if they drift apart.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import create_app  # noqa: E402

OUTPUT = ROOT / "docs" / "api" / "openapi.json"


def contract() -> str:
    return json.dumps(create_app("sqlite://").openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    OUTPUT.write_text(contract(), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
