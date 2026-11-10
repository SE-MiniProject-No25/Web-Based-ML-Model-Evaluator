"""Measure how long POST /api/evaluations takes to acknowledge a valid request (NFR-02, TC-19).

Sends valid evaluation requests one after another to a running server and records how long each
takes to return its ``202``. The reference classification fixtures from EN-02 are used.

    python scripts/measure_ack_time.py                       # server on http://127.0.0.1:8000
    python scripts/measure_ack_time.py --url http://127.0.0.1:8010 --runs 10 --out ack_times.md

Exit status is 0 when every request was acknowledged within the limit, 1 otherwise, so it can run in a
pipeline. The table it prints is what goes into the Test Report.
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

import httpx

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "classification"
DEFAULT_LIMIT_SECONDS = 2.0


def measure(base_url: str, runs: int = 10) -> list[float]:
    """Acknowledgement time in seconds for each of ``runs`` valid requests."""
    model = (FIXTURES / "model.joblib").read_bytes()
    dataset = (FIXTURES / "data.csv").read_bytes()
    times = []
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for _ in range(runs):
            started = time.perf_counter()
            response = client.post(
                "/api/evaluations",
                data={"task_type": "classification", "target_column": "label"},
                files={"model": ("model.joblib", model), "dataset": ("data.csv", dataset)},
            )
            elapsed = time.perf_counter() - started
            if response.status_code != 202:
                detail = response.text[:200]
                raise RuntimeError(f"expected 202 Accepted, got {response.status_code}: {detail}")
            times.append(elapsed)
    return times


def format_report(times: list[float], limit: float) -> str:
    lines = ["| Request | Acknowledgement time (s) | Within limit |", "|---|---|---|"]
    for number, seconds in enumerate(times, start=1):
        lines.append(f"| {number} | {seconds:.3f} | {'yes' if seconds < limit else 'NO'} |")
    lines.append("")
    lines.append(
        f"Limit {limit:.1f} s. Slowest {max(times):.3f} s, mean {statistics.mean(times):.3f} s, "
        f"median {statistics.median(times):.3f} s over {len(times)} requests."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="base URL of a running server")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--limit", type=float, default=DEFAULT_LIMIT_SECONDS, help="seconds")
    parser.add_argument("--out", help="also write the table to this file")
    args = parser.parse_args()

    try:
        times = measure(args.url, args.runs)
    except httpx.ConnectError:
        print(f"Could not connect to {args.url}. Start the backend first (see the README).", file=sys.stderr)
        return 2

    report = format_report(times, args.limit)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
    return 0 if all(t < args.limit for t in times) else 1


if __name__ == "__main__":
    sys.exit(main())
