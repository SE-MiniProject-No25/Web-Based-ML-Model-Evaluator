"""Run the test suite with coverage and write the four Part-3 reports into ../docs (Part 3 deliverables).

    python scripts/generate_reports.py                 # run everything (about 5 minutes) and write the reports
    python scripts/generate_reports.py --reuse DIR     # rebuild the reports from a previous run's files in DIR

Writes docs/Unit_Test_Report.md, docs/System_Validation_Report.md, docs/Code_Coverage_Report.md,
docs/Branch_Coverage_Report.md and the browsable docs/coverage_html/. Every number in them comes from the run.
"""

import argparse
import datetime
import importlib.metadata
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from scripts.measure_ack_time import measure  # noqa: E402
from scripts.tc_report import case_result  # noqa: E402
from tests.conftest import SYSTEM_TEST_FILES  # noqa: E402
from tests.traceability import AUTOMATED, NOT_AUTOMATED  # noqa: E402

# What each test file is about, for the per-file tables.
PURPOSE = {
    "test_config.py": "Settings and environment overrides",
    "test_errors.py": "Error type, status table, safe error responses (US-09)",
    "test_storage.py": "Temporary storage, permissions, retention cleanup (US-10)",
    "test_result_service.py": "Result Service: lifecycle, IDs, concurrency",
    "test_metrics_service.py": "Metrics Service: classification and regression metrics",
    "test_auth.py": "Optional API-key authentication middleware (US-11)",
    "test_architecture.py": "Component boundaries (NFR-09)",
    "test_traceability.py": "Test Plan cases map to real tests",
    "test_reference_fixtures.py": "Shared reference models and datasets (EN-02)",
    "test_worker.py": "Model worker process: every outcome it can report (US-04)",
    "test_model_inspector.py": "Model inspector run during validation (US-07)",
    "test_validation_service.py": "Dataset parsing and child-process handling in validation",
    "test_component_edges.py": "Storage lifecycle edges, metrics, child environment, settings",
    "test_edge_paths.py": "Failed partial write, framework 5xx error, authentication settings lookup, lifespan events",
    "test_api_submit.py": "POST /api/evaluations: validation, limits, filenames (US-01, US-06 to US-08)",
    "test_api_status.py": "GET /api/evaluations/{id} (US-02)",
    "test_api_download.py": "GET /api/evaluations/{id}/download (US-03)",
    "test_acceptance.py": "Reference model and data through the API (TC-08, TC-09)",
    "test_evaluation_runner.py": "Runner with a real model run in a child process (EN-06)",
    "test_evaluation_limits.py": "Incompatible inputs, time and memory limits, safe failures (US-04)",
    "test_failure_paths.py": "Worker dying, half-failed uploads",
    "test_ack_time.py": "Acknowledgement time against a real server (TC-19)",
    "test_demo_script.py": "Every demo scenario behaves as scripted (EN-08)",
    "test_determinism.py": "Identical runs give identical metrics (TC-20)",
    "test_openapi.py": "API documentation matches the contract (EN-07)",
    "test_app.py": "Application starts, health check",
}


def sh(command, **kwargs):
    return subprocess.run(command, cwd=BACKEND, text=True, capture_output=True, **kwargs)


# --- running -------------------------------------------------------------------------------------------


def run_suite(work: Path, html_dir: Path) -> None:
    """One full run with coverage, and one unit-only run with coverage."""
    base = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--cov=app", "--cov-branch"]
    full_env = {**os.environ, "COVERAGE_FILE": str(work / ".coverage_all")}
    print("running all tests with coverage (several minutes)...", flush=True)
    subprocess.run(
        [*base, f"--junitxml={work / 'all.xml'}", f"--cov-report=xml:{work / 'cov_all.xml'}",
         f"--cov-report=html:{html_dir}"],
        cwd=BACKEND, env=full_env, check=False, stdout=subprocess.DEVNULL,
    )  # fmt: skip
    # coverage.py writes a .gitignore containing "*" into its HTML folder, which would keep the report out of git.
    (html_dir / ".gitignore").unlink(missing_ok=True)
    print("running unit tests only with coverage...", flush=True)
    unit_env = {**os.environ, "COVERAGE_FILE": str(work / ".coverage_unit")}
    subprocess.run(
        [*base, "-m", "unit", f"--junitxml={work / 'unit.xml'}", f"--cov-report=xml:{work / 'cov_unit.xml'}"],
        cwd=BACKEND, env=unit_env, check=False, stdout=subprocess.DEVNULL,
    )  # fmt: skip


def measure_ack_times() -> list[float]:
    """Start a real server and time 10 valid submissions, as in TC-19."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    storage = tempfile.mkdtemp()
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=BACKEND, env={**os.environ, "MLEVAL_STORAGE_DIR": storage},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    try:
        import httpx

        for _ in range(100):
            try:
                if httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.2)
        return measure(f"http://127.0.0.1:{port}", runs=10)
    finally:
        server.kill()
        server.wait()
        shutil.rmtree(storage, ignore_errors=True)


# --- reading results -------------------------------------------------------------------------------------


def junit_cases(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    cases = []
    for case in suite.iter("testcase"):
        outcome, note = "passed", ""
        for tag, label in (("failure", "failed"), ("error", "failed"), ("skipped", "skipped")):
            found = case.find(tag)
            if found is not None:
                outcome, note = label, (found.get("message") or "")[:160]
        file = case.get("classname", "").replace(".", "/") + ".py"
        cases.append({"file": Path(file).name, "name": case.get("name", ""), "outcome": outcome,
                      "time": float(case.get("time", 0)), "note": note})  # fmt: skip
    return cases


def level_of(case: dict) -> str:
    return "System" if case["file"] in SYSTEM_TEST_FILES else "Unit"


def counts(cases) -> dict:
    return {k: sum(1 for c in cases if c["outcome"] == k) for k in ("passed", "failed", "skipped")} | {
        "total": len(cases), "seconds": sum(c["time"] for c in cases)  # fmt: skip
    }


def read_coverage(path: Path) -> dict:
    """Per-file and total line and branch coverage from a Cobertura XML file."""
    root = ET.parse(path).getroot()
    files, totals = {}, {"lines": 0, "lines_hit": 0, "branches": 0, "branches_hit": 0}
    for cls in root.iter("class"):
        name = "app/" + cls.get("filename").replace("\\", "/")
        lines, hit, branches, branches_hit = 0, 0, 0, 0
        missed_lines, partial = [], []
        for line in cls.iter("line"):
            number, hits = int(line.get("number")), int(line.get("hits"))
            lines += 1
            hit += hits > 0
            if hits == 0:
                missed_lines.append(number)
            if line.get("branch") == "true":
                match = re.search(r"\((\d+)/(\d+)\)", line.get("condition-coverage", ""))
                taken, total = int(match.group(1)), int(match.group(2))
                branches += total
                branches_hit += taken
                if taken < total:
                    partial.append((number, line.get("missing-branches", ""), taken, total))
        files[name] = {"lines": lines, "hit": hit, "branches": branches, "branches_hit": branches_hit,
                       "missed_lines": missed_lines, "partial": partial}  # fmt: skip
        totals["lines"] += lines
        totals["lines_hit"] += hit
        totals["branches"] += branches
        totals["branches_hit"] += branches_hit
    return {"files": files, "total": totals}


def pct(part: int, whole: int) -> str:
    return "100%" if whole == 0 else f"{100 * part / whole:.1f}%"


def ranges(numbers: list[int]) -> str:
    """[3,4,5,9] -> '3-5, 9'."""
    out, start = [], None
    for index, n in enumerate(numbers):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}-{prev}" if prev != start else str(start))
            start = prev = n
        if index == len(numbers) - 1:
            out.append(f"{start}-{prev}" if prev != start else str(start))
    return ", ".join(out) if out else "none"


def environment() -> dict:
    def version(name):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return "n/a"

    commit = sh(["git", "rev-parse", "--short=8", "HEAD"]).stdout.strip()
    return {
        "date": datetime.date.today().strftime("%d %B %Y").lstrip("0"),
        "commit": commit,
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "pytest": version("pytest"), "coverage": version("coverage"), "fastapi": version("fastapi"),
        "sklearn": version("scikit-learn"),
    }  # fmt: skip


def header(title: str, env: dict, extra: str = "") -> str:
    return (
        f"# {title}\n## Web-Based ML Model Evaluator\n\n"
        f"| | |\n|---|---|\n| **Date** | {env['date']} |\n| **Code** | `main` at commit `{env['commit']}`, plus the tests and documents added by the pull request that contains these reports |\n"
        f"| **Environment** | {env['os']}, Python {env['python']}, pytest {env['pytest']}, "
        f"coverage.py {env['coverage']}, FastAPI {env['fastapi']}, scikit-learn {env['sklearn']} |\n"
        f"| **Reproduce** | `cd backend`, `pip install -r requirements-dev.txt`, `python scripts/generate_reports.py` |\n"
        f"{extra}\n"
    )


SCOPE_NOTE = (
    "**Scope.** These reports cover the backend (`backend/app`). The frontend has no automated tests, so it has "
    "no unit-test or coverage figures; it was checked by hand against a running backend (System Validation "
    "Report, section 6). Adding frontend tests is listed as a defect (DEF-08).\n"
)


# Why a line or branch is not exercised, reviewed by hand. Keyed by file; each entry is
# (range of line numbers, reason). Anything missing from here is printed as NOT YET REVIEWED, so a new
# gap cannot slip into a report unexplained.
REASONS: dict[str, list] = {
    "app/api/auth.py": [
        (range(97, 102), "Handlers for header text that cannot be encoded. HTTP headers are decoded as Latin-1, so a request cannot reach them; kept as a safety net."),
        (range(63, 64), "A token that is empty after trimming cannot occur: splitting the header on whitespace never leaves one. A dead check kept as a safety net."),
        (range(126, 127), "The request always carries its application, so the fall-through to the environment is only reachable when the middleware runs outside Starlette."),
    ],
    "app/evaluation/worker.py": [
        (range(32, 34), "POSIX only: applying the memory limit needs the `resource` module, which Windows does not have. Runs in the Linux CI job."),
        (range(87, 89), "The `if __name__ == \"__main__\"` entry point. The system tests run it as a child process, which coverage does not follow."),
    ],
    "app/validation/model_inspector.py": [
        (range(37, 39), "The `if __name__ == \"__main__\"` entry point. The system tests run it as a child process, which coverage does not follow."),
    ],
    "app/storage/temp_storage.py": [
        (range(41, 43), "Ignoring a failed permission change: only happens on file systems that do not support it."),
        (range(49, 51), "Ignoring a failed permission change: only happens on file systems that do not support it."),
        (range(59, 61), "A safety check that a random UUID filename can never trigger."),
        (range(64, 68), "Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs)."),
        (range(79, 81), "A second failure while removing a partly written file (the first failure is tested); not reproducible reliably."),
    ],
}


def reason_for(name: str, line: int) -> str:
    for span, text in REASONS.get(name, []):
        if line in span:
            return text
    return "NOT YET REVIEWED"


# --- the reports-------------------------------------------------------------------------------------------


def unit_report(env, all_cases, unit_cov) -> str:
    unit = [c for c in all_cases if level_of(c) == "Unit"]
    system = [c for c in all_cases if level_of(c) == "System"]
    u = counts(unit)
    out = [header("Unit Test Report", env), SCOPE_NOTE]
    out.append(
        "## 1. What counts as a unit test\n\nA **unit test** checks one component on its own: pure functions, a "
        "component with in-memory fakes, or a small application built inside the test. A **system test** goes "
        "through the whole application (the HTTP API, a real server, or a real model run in a child process); "
        "those are reported in the [System Validation Report](System_Validation_Report.md). The split is made "
        "once, in `backend/tests/conftest.py`, and tests carry the pytest markers `unit` and `system`.\n"
    )
    out.append(
        "## 2. Summary\n\n| | Unit | System | All |\n|---|---|---|---|\n"
        f"| Tests | {u['total']} | {len(system)} | {len(all_cases)} |\n"
        f"| Passed | {u['passed']} | {counts(system)['passed']} | {counts(all_cases)['passed']} |\n"
        f"| Failed | {u['failed']} | {counts(system)['failed']} | {counts(all_cases)['failed']} |\n"
        f"| Skipped | {u['skipped']} | {counts(system)['skipped']} | {counts(all_cases)['skipped']} |\n"
        f"| Run time | {u['seconds']:.1f} s | {counts(system)['seconds']:.0f} s | {counts(all_cases)['seconds']:.0f} s |\n"
    )
    t = unit_cov["total"]
    out.append(
        f"\nThe unit tests alone cover **{pct(t['lines_hit'], t['lines'])} of lines** and "
        f"**{pct(t['branches_hit'], t['branches'])} of branches** of `backend/app` and run in about "
        f"{u['seconds']:.0f} seconds. See the [Code Coverage Report](Code_Coverage_Report.md) and the "
        "[Branch Coverage Report](Branch_Coverage_Report.md).\n"
    )
    rows = ["| Test file | Component under test | Tests | Passed | Failed | Skipped |", "|---|---|---|---|---|---|"]
    for file in sorted({c["file"] for c in unit}):
        subset = [c for c in unit if c["file"] == file]
        k = counts(subset)
        rows.append(f"| `{file}` | {PURPOSE.get(file, '')} | {k['total']} | {k['passed']} | {k['failed']} | {k['skipped']} |")
    out.append("## 3. Results by test file\n\n" + "\n".join(rows) + "\n")
    skipped = [c for c in unit if c["outcome"] == "skipped"]
    failed = [c for c in unit if c["outcome"] == "failed"]
    out.append("## 4. Failures and skipped tests\n")
    out.append("No unit test failed.\n" if not failed else "Failed: " + ", ".join(f"`{c['name']}`" for c in failed) + "\n")
    if skipped:
        out.append("Skipped:\n\n" + "\n".join(f"- `{c['file']}::{c['name']}`: {c['note'] or 'skipped'}" for c in skipped) + "\n")
        out.append("These need the POSIX `resource` module, so they only run on Linux and macOS (they run in CI).\n")
    out.append(
        "## 5. What the unit tests cover well\n\n"
        "- **Security-relevant code paths:** a hung or crashing model-inspection child, a worker killed without "
        "reporting, a half-failed upload that must not leave files behind, child-process environment without "
        "server secrets, path traversal in stored filenames, authentication edge cases, and error responses that "
        "must not leak internals.\n"
        "- **The model worker and inspector** run in child processes during real use, which coverage cannot "
        "follow, so they are called in-process by `test_worker.py` and `test_model_inspector.py`. That is why "
        "they have real coverage figures.\n"
        "- **Component boundaries** are enforced by `test_architecture.py` (NFR-09).\n"
    )
    out.append(
        "## 6. Known gaps\n\n"
        "- No frontend unit tests (DEF-08).\n"
        "- Memory-limit behaviour is only exercised on Linux and macOS.\n"
        "- Lines that remain uncovered are listed per file in the Code Coverage Report, each with a reason.\n"
    )
    return "\n".join(out)


def coverage_report(env, cov_all, cov_unit) -> str:
    t, tu = cov_all["total"], cov_unit["total"]
    out = [header("Code Coverage Report", env), SCOPE_NOTE]
    out.append(
        "## 1. Summary\n\nLine coverage is the share of executable statements that ran at least once.\n\n"
        "| Run | Statements | Covered | Line coverage |\n|---|---|---|---|\n"
        f"| **All tests** (unit and system) | {t['lines']} | {t['lines_hit']} | **{pct(t['lines_hit'], t['lines'])}** |\n"
        f"| Unit tests only | {tu['lines']} | {tu['lines_hit']} | {pct(tu['lines_hit'], tu['lines'])} |\n"
    )
    rows = ["| File | Statements | Covered | Line coverage | Unit tests only | Uncovered lines |", "|---|---|---|---|---|---|"]
    for name, f in sorted(cov_all["files"].items()):
        fu = cov_unit["files"].get(name, {"lines": f["lines"], "hit": 0})
        rows.append(
            f"| `{name}` | {f['lines']} | {f['hit']} | {pct(f['hit'], f['lines'])} | {pct(fu['hit'], fu['lines'])} | "
            f"{ranges(f['missed_lines'])} |"
        )
    out.append("## 2. Line coverage by file\n\n" + "\n".join(rows) + "\n")
    out.append(
        "The files are in `backend/app`. A browsable, line-by-line version with the uncovered lines highlighted "
        "is in [`coverage_html/index.html`](coverage_html/index.html).\n"
    )
    out.append("## 3. Why some lines are not covered\n")
    rows = ["| File | Lines | Reason |", "|---|---|---|"]
    unreviewed = 0
    for name, f in sorted(cov_all["files"].items()):
        by_reason: dict[str, list[int]] = {}
        for line in f["missed_lines"]:
            by_reason.setdefault(reason_for(name, line), []).append(line)
        for reason, lines in by_reason.items():
            unreviewed += reason == "NOT YET REVIEWED"
            rows.append(f"| `{name}` | {ranges(lines)} | {reason} |")
    out.append(
        ("\n".join(rows) if len(rows) > 2 else "Every statement was executed.") + "\n\n"
        "Code that only runs inside child processes (the model worker and inspector) is measured through the "
        "in-process unit tests (`test_worker.py`, `test_model_inspector.py`); the system tests run it for real but "
        "coverage cannot follow into the child, so it is not counted twice. Lines marked *POSIX only* run in the "
        "Linux CI job, not on a Windows laptop.\n"
    )
    if unreviewed:
        print(f"WARNING: {unreviewed} uncovered block(s) have no reviewed reason", file=sys.stderr)
    out.append(
        "## 4. How to reproduce\n\n```bash\ncd backend\npip install -r requirements-dev.txt\n"
        "pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html\n```\n"
    )
    return "\n".join(out)


def branch_report(env, cov_all, cov_unit) -> str:
    t, tu = cov_all["total"], cov_unit["total"]
    out = [header("Branch Coverage Report", env), SCOPE_NOTE]
    out.append(
        "## 1. Summary\n\nA branch is one outcome of a decision (the `if` taken, or not taken; a loop entered, or "
        "skipped). Branch coverage is the share of those outcomes that ran at least once.\n\n"
        "| Run | Branches | Covered | Branch coverage |\n|---|---|---|---|\n"
        f"| **All tests** (unit and system) | {t['branches']} | {t['branches_hit']} | **{pct(t['branches_hit'], t['branches'])}** |\n"
        f"| Unit tests only | {tu['branches']} | {tu['branches_hit']} | {pct(tu['branches_hit'], tu['branches'])} |\n"
    )
    combined = (t["lines_hit"] + t["branches_hit"], t["lines"] + t["branches"])
    out.append(f"\nLines and branches combined (the figure coverage.py prints as *Cover*): **{pct(*combined)}**.\n")
    rows = ["| File | Branches | Covered | Branch coverage | Unit tests only |", "|---|---|---|---|---|"]
    for name, f in sorted(cov_all["files"].items()):
        if f["branches"] == 0:
            continue
        fu = cov_unit["files"].get(name, {"branches": f["branches"], "branches_hit": 0})
        rows.append(f"| `{name}` | {f['branches']} | {f['branches_hit']} | {pct(f['branches_hit'], f['branches'])} | {pct(fu['branches_hit'], fu['branches'])} |")
    out.append("## 2. Branch coverage by file\n\n" + "\n".join(rows) + "\n")
    partial_rows = ["| File | Line | Branches taken | Not taken (goes to line) | Reason |", "|---|---|---|---|---|"]
    count = unreviewed = 0
    for name, f in sorted(cov_all["files"].items()):
        for number, missing, taken, total in f["partial"]:
            reason = reason_for(name, number)
            unreviewed += reason == "NOT YET REVIEWED"
            partial_rows.append(f"| `{name}` | {number} | {taken} of {total} | {missing or 'exit'} | {reason} |")
            count += 1
    out.append(
        f"## 3. Branches never taken\n\n{count} decision outcomes were never exercised by any test "
        "(lines where a branch is only partly taken). Each was reviewed:\n\n" + "\n".join(partial_rows) + "\n"
    )
    if unreviewed:
        print(f"WARNING: {unreviewed} untaken branch(es) have no reviewed reason", file=sys.stderr)
    out.append(
        "## 4. How to reproduce\n\n```bash\ncd backend\npytest --cov=app --cov-branch --cov-report=term-missing\n```\n"
        "The *BrPart* column in that output is the same data as section 3.\n"
    )
    return "\n".join(out)


def validation_report(env, all_cases, cov_all, ack_times) -> str:
    outcomes = {}
    for case in all_cases:
        outcomes.setdefault((f"tests/{case['file']}", case["name"].split("[")[0]), []).append(case["outcome"])
    results = {}
    for case_id in sorted(set(AUTOMATED) | set(NOT_AUTOMATED)):
        if case_id in AUTOMATED:
            results[case_id] = case_result(AUTOMATED[case_id], outcomes)
    passed = sorted([c for c, (r, _) in results.items() if r == "PASS"] + ["TC-21"])  # TC-21 is a manual pass
    failed = sorted(c for c, (r, _) in results.items() if r == "FAIL")
    k = counts(all_cases)
    slowest, mean = max(ack_times), sum(ack_times) / len(ack_times)
    out = [header("System Validation Report", env), SCOPE_NOTE]
    out.append(
        "Result of executing the [Test Plan](../deliverable-1/02_Test_Plan.md) (25 cases, TC-01 to TC-25) against the "
        "complete application. It replaces `planning/Test_Report.md` (3 November), which was written before "
        "authentication, safe error responses, secure storage, the determinism tests and the usability test were merged.\n"
    )
    out.append(
        "## 1. Summary\n\n| Result | Cases |\n|---|---|\n"
        f"| **Pass** | **{len(passed)} of 25**: {', '.join(passed)}. 24 are automated; TC-21 is a manual test with one participant |\n"
        f"| **Fail** | {len(failed)}{(': ' + ', '.join(failed)) if failed else ''} |\n"
        "| Of those, with a limitation | "
        "TC-15 (memory limit not enforced on Windows), TC-18 (cleanup runs on the next submission, not on a timer), "
        "TC-21 (see section 5) |\n\n"
        f"The automated suite has {k['total']} tests: {k['passed']} passed, {k['failed']} failed, {k['skipped']} skipped "
        "(the memory-limit tests only run on Linux, in CI). Since the previous report, authentication (TC-17) "
        "and cleanup of temporary files (TC-18) have been built and now pass, so the two failures recorded then "
        "are closed.\n"
    )
    case_rows = {
        "TC-01": "Upload model", "TC-02": "Upload dataset", "TC-03": "Unsupported file", "TC-04": "Size limit boundary",
        "TC-05": "Missing target column", "TC-06": "Invalid task type", "TC-07": "Empty submission",
        "TC-08": "Classification metrics", "TC-09": "Regression metrics", "TC-10": "Status lifecycle",
        "TC-11": "Incompatible inputs", "TC-12": "Download", "TC-13": "Path-like filename",
        "TC-14": "Malformed model", "TC-15": "Resource limits", "TC-16": "No sensitive errors",
        "TC-17": "Authentication", "TC-18": "Temporary cleanup", "TC-19": "Acknowledgement time",
        "TC-20": "Determinism", "TC-21": "Usability", "TC-22": "Unique ID, terminal state",
        "TC-23": "Malformed CSV", "TC-24": "Unknown ID", "TC-25": "Download too early",
    }
    notes = {
        "TC-01": "API accepts a supported model. UI checked by hand (section 6).",
        "TC-02": "API accepts a valid CSV; the UI lists the detected columns (section 6).",
        "TC-07": "Each missing field gives `400 MISSING_REQUIRED_FIELD`. In the UI the Next button stays disabled (section 6).",
        "TC-12": "Download works through the API and through the interface's Download Results button (section 6).",
        "TC-15": "Time limit proven end to end; memory limit proven on Linux (CI) and not enforced on Windows (DEF-04).",
        "TC-16": "Validation errors, runtime errors, unknown URLs and unexpected exceptions leak no trace, secret or path.",
        "TC-17": "Optional API key (`X-API-Key` or `Authorization: Bearer`); fails secure if enabled with no key.",
        "TC-18": "Expired files are removed. The sweep runs when a new evaluation is submitted, not on a timer (DEF-02, DEF-10).",
        "TC-19": f"Slowest of 10: {slowest:.2f} s against the 2 s limit (section 3).",
        "TC-20": "Three identical runs give identical metrics, classification and regression.",
        "TC-21": "A person outside the team completed the workflow unaided; see section 5 for the caveats.",
    }
    rows = ["| Case | What | Result | Automated tests passed | Note |", "|---|---|---|---|---|"]
    for case_id in sorted(case_rows):
        if case_id in results:
            result, detail = results[case_id]
        else:
            result, detail = "MANUAL", "-"
        shown = {"PASS": "Pass", "FAIL": "**Fail**", "MANUAL": "Pass (manual)", "SKIPPED": "Skipped"}[result]
        rows.append(f"| {case_id} | {case_rows[case_id]} | {shown} | {detail} | {notes.get(case_id, '')} |")
    out.append("## 2. Results by test case\n\n" + "\n".join(rows) + "\n\n"
               "Which tests cover each case is recorded in `backend/tests/traceability.py` and checked by "
               "`tests/test_traceability.py`.\n")
    ack_rows = " | ".join(f"{t:.3f}" for t in ack_times)
    out.append(
        "## 3. Performance (TC-19, NFR-02)\n\n10 valid requests one after another against a local server, "
        "seconds until the `202`:\n\n| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |\n|---|---|---|---|---|---|---|---|---|---|\n"
        f"| {ack_rows} |\n\nSlowest {slowest:.3f} s, mean {mean:.3f} s; the limit is 2 s. "
        + ("All are within the limit" if slowest < 2 else "**The limit was exceeded**")
        + f", with {(2 - slowest):.2f} s to spare in the worst case. Almost all of the time is the model check done "
        "before the `202` (a child process loads scikit-learn to open the model), see DEF-05. The figure varies from "
        "run to run: on 10 November three further runs on an otherwise idle machine had slowest times of 1.74, 1.72 "
        "and 1.82 s, and this run, which started right after the test suite, 1.89 s. Treat the margin as roughly "
        "0.1 to 0.3 s on this laptop.\n"
    )
    out.append(
        "## 4. Determinism (TC-20, NFR-03)\n\nThe tests in `tests/test_determinism.py` submit the same model and "
        "dataset three times for classification and for regression and require identical metrics. Both pass.\n"
    )
    out.append(
        "## 5. Usability (TC-21, NFR-01)\n\nThe usability test is written up in "
        "[`deliverable-1/usability-testing/US-22_Usability_Test_Report.md`](../deliverable-1/usability-testing/US-22_Usability_Test_Report.md). "
        "One person outside the team completed the workflow (upload, configure, evaluate, inspect the result) in about "
        "two minutes without help, and found the evaluate button easily. Improvement suggestions: clearer guidance "
        "on which files to choose, plain-language descriptions of the options, and explanations of the metrics.\n\n"
        "Two things in that report need correcting before it is relied on:\n\n"
        "- It says the participant \"did not notice the download control\". The interface only gained a download "
        "button on 10 November (pull request #62), and the report has no date, so it cannot be tied to a build; if "
        "an earlier build was tested there was nothing to notice. The author should say which build was used.\n"
        "- The test date is still the placeholder `[Enter actual test date]`.\n\n"
        "With one participant this is an indication, not a statistically meaningful result. TC-21 is recorded as a "
        "**pass** for the primary workflow, with those caveats (DEF-07).\n"
    )
    out.append(
        "## 6. The user interface in a real browser\n\nThe browser half of TC-01, TC-02, TC-07, TC-08, TC-09, TC-11 and "
        "TC-12 is automated in `e2e/test_workflow.py` (TEST-07): Playwright drives Chromium against the real frontend "
        "and a real backend started for the run, with the demo inputs, and the tests run in CI. They check that:\n\n"
        "- a classification run and a regression run show their metrics in the table (with the explanations) and the chart, with the expected values;\n"
        "- **Download Results** saves `evaluation-<id>.json` with the status, the target column and the same accuracy as the screen;\n"
        "- a malformed CSV is rejected and the message is shown next to the dataset field, with no download offered;\n"
        "- a mismatched dataset ends *failed* with a message naming the missing and unused columns;\n"
        "- a `.txt` model is refused as soon as it is chosen, and the next step stays disabled;\n"
        "- with the backend unreachable, submitting shows \"Unable to connect to the evaluation server\".\n\n"
        "Run them with `python -m pytest e2e` (see the README). The component tests in `frontend/src/test/` cover the "
        "same screens at a finer grain (TEST-01).\n"
    )
    out.append(
        "## 7. Security validation (Test Plan 5.1)\n\n| Area | Result |\n|---|---|\n"
        "| File validation | Pass: unsupported and malformed files rejected before execution (TC-03, TC-14, TC-23) |\n"
        "| Size limits | Pass (TC-04) |\n| Path handling | Pass (TC-13) |\n"
        "| Input validation | Pass: task type and target checked on the server (TC-05, TC-06) |\n"
        "| Resource protection | Pass on Linux and macOS; time limit only on Windows (TC-15, DEF-04) |\n"
        "| Error disclosure | Pass (TC-16): standard error format everywhere, including unknown URLs and unexpected exceptions |\n"
        "| Temporary data | Pass with a limitation (TC-18, DEF-02) |\n"
        "| Authentication | Pass (TC-17); off by default, so a deployment must switch it on |\n\n"
        "Accepted limitation, documented in the README: a model file is a pickle and runs code when loaded. Models are "
        "only opened in a child process with a sanitized environment and limits. That is process isolation, not a "
        "sandbox (DEF-06).\n"
    )
    exe_ok = [
        ("All mandatory test cases have been executed", "Yes. All 25 were executed; TC-21 as a manual test."),
        ("Critical functional requirements have passing tests or documented defects",
         "Yes. FR-01 to FR-20 pass at the API, and FR-15 also in the interface (Download Results button)."),
        ("Security validation cases have been executed", "Yes. TC-03, TC-04, TC-13 to TC-18 and TC-23 all pass."),
        ("Traceability is complete", "Yes. All 25 cases map to tests or a manual record, checked automatically."),
        ("Unresolved defects are documented with severity and status", "Yes, section 8."),
    ]
    out.append("## 8. Exit criteria (Test Plan 4.3)\n\n| Criterion | Met? |\n|---|---|\n"
               + "\n".join(f"| {c} | {m} |" for c, m in exe_ok) + "\n\n"
               "The exit criteria are met. Open defects are low or medium severity, except the accepted pickle limitation.\n")
    out.append(
        "## 9. Defects\n\n| ID | Defect | Severity | Status |\n|---|---|---|---|\n"
        "| DEF-01 | Authentication not enforced | High | **Closed** by US-11 (pull request #58); TC-17 passes |\n"
        "| DEF-02 | Uploaded files were never deleted | High | **Closed with a limitation**: US-10 (#57) removes expired files, but only when a new evaluation is submitted; with no new requests they stay until the next one. Low severity now |\n"
        "| DEF-03 | Unknown URLs returned the framework's default error body | Low | **Closed** by US-09 (#56); verified: `GET /api/nope` gives `404 {\"error\": {\"code\": \"NOT_FOUND\", ...}}` |\n"
        "| DEF-04 | Memory limit not enforced on Windows | Medium | Accepted, documented in the README |\n"
        f"| DEF-05 | Acknowledgement margin is small on Windows ({slowest:.2f} s of 2 s), dominated by the model check before the `202` | Low | Open, monitor |\n"
        "| DEF-06 | A malicious model still runs code with the server user's privileges (pickle) | High (inherent) | Accepted, documented |\n"
        "| DEF-07 | The usability report has no test date, so its remark about a download control cannot be tied to a build | Low | Open, owner Akshya |\n"
        "| DEF-08 | The frontend has no automated tests and no coverage figures | Medium | Open |\n"
        "| DEF-09 | The interface had no control to download results, so TC-12 was only met through the API | Medium | **Closed** by US-17 (pull request #62); verified: the button appears once an evaluation completes and saves `evaluation-<id>.json` with every field |\n"
        "| DEF-10 | The retention cleanup does not skip files of an evaluation that is still running. With the defaults (retention 3600 s, evaluation limit 60 s) this cannot happen, but a retention shorter than a run could delete files mid-evaluation | Low | Open, owner Akash |\n"
    )
    out.append(
        "## 10. Changes to test cases\n\nThe detailed test cases in [Test Plan section 8](../deliverable-1/02_Test_Plan.md) were "
        "updated to match what was built (authentication mechanism, retention, limits, download through the API). "
        "A table in section 9 of the Test Plan links each case to its automated tests.\n"
    )
    return "\n".join(out)


# --- main ---------------------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reuse", help="rebuild the reports from the files of a previous run in this folder")
    parser.add_argument("--out", default=str(REPO / "docs"), help="where to write the reports")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(args.reuse) if args.reuse else Path(tempfile.mkdtemp(prefix="reports-"))
    html_dir = out / "coverage_html"
    if not args.reuse:
        if html_dir.exists():
            shutil.rmtree(html_dir)
        run_suite(work, html_dir)
        (work / "ack.txt").write_text(",".join(str(t) for t in measure_ack_times()))
    ack_times = [float(x) for x in (work / "ack.txt").read_text().split(",")]

    env = environment()
    all_cases = junit_cases(work / "all.xml")
    cov_all, cov_unit = read_coverage(work / "cov_all.xml"), read_coverage(work / "cov_unit.xml")

    (out / "Unit_Test_Report.md").write_text(unit_report(env, all_cases, cov_unit), encoding="utf-8")
    (out / "System_Validation_Report.md").write_text(validation_report(env, all_cases, cov_all, ack_times), encoding="utf-8")
    (out / "Code_Coverage_Report.md").write_text(coverage_report(env, cov_all, cov_unit), encoding="utf-8")
    (out / "Branch_Coverage_Report.md").write_text(branch_report(env, cov_all, cov_unit), encoding="utf-8")
    t = cov_all["total"]
    print(f"wrote 4 reports to {out}: {len(all_cases)} tests, line coverage {pct(t['lines_hit'], t['lines'])}, "
          f"branch coverage {pct(t['branches_hit'], t['branches'])}")  # fmt: skip
    print(f"working files kept in {work}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
