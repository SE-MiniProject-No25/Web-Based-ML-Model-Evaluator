"""Fail when line or branch coverage falls below the agreed thresholds (TEST-03).

    pytest --cov --cov-report=json        # writes coverage.json
    python scripts/check_coverage.py      # exit status 1 if either figure is too low

pytest-cov can only check one combined figure, so line and branch coverage are checked here separately.
"""

import argparse
import json
import sys
from pathlib import Path

LINE_THRESHOLD = 90.0
BRANCH_THRESHOLD = 85.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", default="coverage.json")
    args = parser.parse_args()

    totals = json.loads(Path(args.report).read_text(encoding="utf-8"))["totals"]
    line = 100.0 * totals["covered_lines"] / max(totals["num_statements"], 1)
    branch = 100.0 * totals["covered_branches"] / max(totals["num_branches"], 1)
    ok = line >= LINE_THRESHOLD and branch >= BRANCH_THRESHOLD
    print(f"line coverage {line:.1f}% (minimum {LINE_THRESHOLD}%), branch coverage {branch:.1f}% "
          f"(minimum {BRANCH_THRESHOLD}%): {'ok' if ok else 'TOO LOW'}")  # fmt: skip
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
