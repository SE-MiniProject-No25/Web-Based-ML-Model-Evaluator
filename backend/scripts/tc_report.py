"""Run the test suite and report the result of each Test Plan case (EN-03).

    python scripts/tc_report.py                    # run pytest, then print the table
    python scripts/tc_report.py --junit run.xml    # reuse an existing pytest --junitxml file
    python scripts/tc_report.py --out table.md     # also write the table to a file

Which tests cover which case is defined in tests/traceability.py. The exit status is 1 if any mapped
test failed or is missing, so it can gate a pipeline.
"""

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from tests.traceability import AUTOMATED, NOT_AUTOMATED  # noqa: E402


def run_pytest(junit_path: Path) -> int:
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit_path}"]
    return subprocess.run(command, cwd=BACKEND).returncode


def read_results(junit_path: Path) -> tuple[dict, dict]:
    """({(file, function): [outcomes]}, suite totals) from a pytest junit file."""
    root = ET.parse(junit_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    outcomes: dict[tuple[str, str], list[str]] = {}
    for case in suite.iter("testcase"):
        file = case.get("classname", "").replace(".", "/") + ".py"
        function = case.get("name", "").split("[")[0]
        if case.find("failure") is not None or case.find("error") is not None:
            outcome = "failed"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        outcomes.setdefault((file, function), []).append(outcome)
    totals = {k: suite.get(k, "0") for k in ("tests", "failures", "errors", "skipped", "time")}
    return outcomes, totals


def case_result(test_ids: list[str], outcomes: dict) -> tuple[str, str]:
    """(result, 'passed/total tests') for one case."""
    found = []
    for test_id in test_ids:
        path, _, function = test_id.partition("::")
        found.extend(outcomes.get((path, function), ["missing"]))
    passed, failed = found.count("passed"), found.count("failed")
    skipped, missing = found.count("skipped"), found.count("missing")
    detail = f"{passed}/{len(found)}" + (f", {skipped} skipped" if skipped else "")
    if failed or missing:
        return "FAIL", detail
    return ("PASS" if passed else "SKIPPED"), detail


def build_table(outcomes: dict) -> tuple[str, bool]:
    rows = ["| Case | Result | Tests passed | Note |", "|---|---|---|---|"]
    ok = True
    for case in sorted(set(AUTOMATED) | set(NOT_AUTOMATED)):
        if case in AUTOMATED:
            result, detail = case_result(AUTOMATED[case], outcomes)
            ok &= result != "FAIL"
            rows.append(f"| {case} | {result} | {detail} | |")
        else:
            rows.append(f"| {case} | NOT RUN | - | {NOT_AUTOMATED[case]} |")
    return "\n".join(rows), ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--junit", help="reuse this pytest junit xml instead of running the suite")
    parser.add_argument("--out", help="also write the table to this file")
    args = parser.parse_args()

    if args.junit:
        junit_path = Path(args.junit)
    else:
        junit_path = Path(tempfile.mkdtemp()) / "junit.xml"
        run_pytest(junit_path)

    outcomes, totals = read_results(junit_path)
    table, ok = build_table(outcomes)
    summary = (
        f"\nSuite: {totals['tests']} tests, {totals['failures']} failed, {totals['errors']} errors, "
        f"{totals['skipped']} skipped, {float(totals['time']):.0f} s."
    )
    print(table + summary)
    if args.out:
        Path(args.out).write_text(table + "\n" + summary + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
