"""Keeps the Test Plan's traceability honest: every case is accounted for and every mapped test exists."""

import ast
import re
from pathlib import Path

from tests.traceability import AUTOMATED, NOT_AUTOMATED

BACKEND = Path(__file__).resolve().parents[1]
TEST_PLAN = BACKEND.parent / "deliverable-1" / "02_Test_Plan.md"


def plan_case_ids():
    return sorted(set(re.findall(r"^\| (TC-\d\d) \|", TEST_PLAN.read_text(encoding="utf-8"), re.M)))


def test_the_test_plan_has_25_cases():
    assert len(plan_case_ids()) == 25


def test_every_test_plan_case_is_either_automated_or_explained():
    accounted = set(AUTOMATED) | set(NOT_AUTOMATED)
    assert accounted == set(plan_case_ids())
    assert not set(AUTOMATED) & set(NOT_AUTOMATED), "a case cannot be both automated and not automated"


def test_every_mapped_test_exists():
    problems = []
    for case, test_ids in AUTOMATED.items():
        for test_id in test_ids:
            path, _, function = test_id.partition("::")
            file = BACKEND / path
            if not file.exists():
                problems.append(f"{case}: {path} does not exist")
                continue
            tree = ast.parse(file.read_text(encoding="utf-8"))
            defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            if function not in defined:
                problems.append(f"{case}: {path} has no test named {function}")
    assert problems == []
