"""EN-08: every scenario in planning/Demo_Script.md behaves as the script says (see demo_check.py)."""

import httpx

from scripts.demo_check import run_checks


def test_every_demo_scenario_behaves_as_scripted(server_url):
    with httpx.Client(base_url=server_url, timeout=60.0) as client:
        results = run_checks(client)

    failures = [f"{name}: {detail}" for name, ok, detail in results if not ok]
    assert failures == []
    assert len(results) == 9
