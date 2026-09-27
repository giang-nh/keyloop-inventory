"""Every acceptance criterion in docs/SPEC.md has a test, and every test points to a real one.

Tests name the criterion they prove, for example `test_ac_2_2_day_91_is_aging` proves
AC-2.2. This check reads the spec and the test names and fails the build if either side
is missing. So if the spec changes, the tests have to change with it.
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "SPEC.md"
TESTS = ROOT / "tests"

_SPEC_ID = re.compile(r"^\| (AC-\d+\.\d+) \|", re.MULTILINE)
_TEST_ID = re.compile(r"(?:^|_)ac_(\d+)_(\d+)(?=_|$)")


def criteria_in_spec() -> set[str]:
    return set(_SPEC_ID.findall(SPEC.read_text(encoding="utf-8")))


def criteria_in_tests() -> dict[str, list[str]]:
    """Map each criterion ID to the tests that name it."""
    found: dict[str, list[str]] = {}
    for path in TESTS.rglob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                for major, minor in _TEST_ID.findall(node.name):
                    where = f"{path.relative_to(ROOT).as_posix()}::{node.name}"
                    found.setdefault(f"AC-{major}.{minor}", []).append(where)
    return found


def test_the_spec_has_acceptance_criteria():
    assert len(criteria_in_spec()) >= 25


def test_every_acceptance_criterion_has_at_least_one_test():
    missing = sorted(criteria_in_spec() - set(criteria_in_tests()))

    assert not missing, f"No test proves: {', '.join(missing)}"


def test_every_test_points_to_a_criterion_that_exists():
    unknown = {
        ac: tests for ac, tests in criteria_in_tests().items() if ac not in criteria_in_spec()
    }

    assert not unknown, f"Tests name criteria that are not in SPEC.md: {unknown}"
