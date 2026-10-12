#!/usr/bin/env python3
"""Draw a sprint burndown chart (SVG) from the team's GitHub Project.

Remaining points on a day = the sprint's total Estimate minus the Estimate of every issue that was done by the
end of that day. An issue counts as done on the day it was closed, or (if it was moved to Done without being
closed) the day its project card was last updated. Re-run the script after issues move to Done to refresh it.

Needs the GitHub CLI logged in with the `project` scope:  gh auth refresh -h github.com -s project

    python3 planning/burndown/burndown.py                       # Sprint 1, Adyanth-212's issues
    python3 planning/burndown/burndown.py --owner all           # whole team
    python3 planning/burndown/burndown.py --sprint "Sprint 2"
"""
import argparse, datetime as dt, json, math, os, subprocess
from xml.sax.saxutils import escape

ORG, PROJECT_NUMBER = "SE-MiniProject-No25", 1
QUERY = """
query($org: String!, $n: Int!) { organization(login: $org) { projectV2(number: $n) {
  fields(first: 30) { nodes { ... on ProjectV2IterationField { configuration {
      iterations { title startDate duration } completedIterations { title startDate duration } } } } }
  items(first: 100) { nodes {
    updatedAt
    content { ... on Issue { number title state closedAt assignees(first: 5) { nodes { login } } } }
    fieldValues(first: 20) { nodes {
      ... on ProjectV2ItemFieldIterationValue { title field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
      ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } } } } } } } } }
"""


def fetch():
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"org={ORG}", "-F", f"n={PROJECT_NUMBER}"],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"gh api failed (is the `project` scope granted?):\n{out.stderr or out.stdout}")
    return json.loads(out.stdout)["data"]["organization"]["projectV2"]


def local_date(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date()


def load(project, sprint, owner):
    its = [i for f in project["fields"]["nodes"] if f.get("configuration")
           for i in f["configuration"]["iterations"] + f["configuration"]["completedIterations"]]
    it = next((i for i in its if i["title"] == sprint), None)
    if not it:
        raise SystemExit(f"No iteration called {sprint!r}; found {[i['title'] for i in its]}")
    start = dt.date.fromisoformat(it["startDate"])
    issues = []
    for node in project["items"]["nodes"]:
        c = node["content"]
        if not c or "number" not in c:
            continue
        vals = {v["field"]["name"]: v for v in node["fieldValues"]["nodes"] if v and v.get("field")}
        if vals.get("Iteration", {}).get("title") != sprint:
            continue
        who = [a["login"] for a in c["assignees"]["nodes"]]
        if owner != "all" and owner not in who:
            continue
        status = vals.get("Status", {}).get("name", "Todo")
        done = None
        if c["state"] == "CLOSED" and c["closedAt"]:
            done = local_date(c["closedAt"])
        elif status == "Done":
            done = local_date(node["updatedAt"])
        issues.append(dict(n=c["number"], title=c["title"], pts=int(vals.get("Estimate", {}).get("number", 0)),
                           status="Done" if done else status, done=done))
    return start, it["duration"], sorted(issues, key=lambda i: i["n"])


def series(issues, start, days, today):
    total = sum(i["pts"] for i in issues)
    def remaining(day):
        return total - sum(i["pts"] for i in issues if i["done"] and i["done"] <= day)
    actual = [remaining(start - dt.timedelta(days=1))]
    for d in range(days):
        day = start + dt.timedelta(days=d)
        if day <= today:
            actual.append(remaining(day))
    ideal = [total * (1 - d / days) for d in range(days + 1)]
    return total, actual, ideal


def svg(title, subtitle, start, days, total, actual, ideal, today):
    W, H, L, R, T, B = 780, 440, 64, 46, 78, 76
    pw, ph = W - L - R, H - T - B
    step = 1 if total <= 12 else 2 if total <= 30 else 5
    ymax = max(step, math.ceil(total / step) * step)
    x = lambda i: L + pw * i / days
    y = lambda v: T + ph * (1 - v / ymax)
    pts = lambda s: " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
         f'<rect width="{W}" height="{H}" rx="10" fill="#ffffff" stroke="#d0d7de"/>',
         f'<text x="{L}" y="32" font-size="19" font-weight="600" fill="#1f2328">{escape(title)}</text>',
         f'<text x="{L}" y="54" font-size="13" fill="#59636e">{escape(subtitle)}</text>']
    for v in range(0, ymax + 1, step):
        o += [f'<line x1="{L}" y1="{y(v):.1f}" x2="{W - R}" y2="{y(v):.1f}" stroke="#eaeef2"/>',
              f'<text x="{L - 10}" y="{y(v) + 4:.1f}" font-size="12" text-anchor="end" fill="#59636e">{v}</text>']
    o.append(f'<text transform="translate(18 {T + ph / 2}) rotate(-90)" font-size="12" text-anchor="middle" '
             f'fill="#59636e">Story points remaining</text>')
    labels = ["Start"] + [(start + dt.timedelta(days=d)).strftime("%a %-d %b") for d in range(days)]
    for i, lab in enumerate(labels):
        o.append(f'<text x="{x(i):.1f}" y="{H - B + 22}" font-size="11" text-anchor="middle" fill="#59636e">{lab}</text>')
    ti = (today - start).days + 1
    if 0 < ti <= days:
        o += [f'<line x1="{x(ti):.1f}" y1="{T}" x2="{x(ti):.1f}" y2="{T + ph}" stroke="#bf8700" stroke-dasharray="2 4"/>',
              f'<text x="{x(ti):.1f}" y="{T - 6}" font-size="11" text-anchor="middle" fill="#9a6700">today</text>']
    o += [f'<polyline points="{pts(ideal)}" fill="none" stroke="#8c959f" stroke-width="2" stroke-dasharray="6 5"/>',
          f'<polyline points="{pts(actual)}" fill="none" stroke="#0969da" stroke-width="3"/>']
    o += [f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4.5" fill="#0969da"/>'
          f'<text x="{x(i):.1f}" y="{y(v) - 10:.1f}" font-size="11" text-anchor="middle" fill="#0550ae">{v:g}</text>'
          for i, v in enumerate(actual)]
    ly = H - 16
    o += [f'<line x1="{L}" y1="{ly - 4}" x2="{L + 28}" y2="{ly - 4}" stroke="#0969da" stroke-width="3"/>',
          f'<text x="{L + 36}" y="{ly}" font-size="12" fill="#1f2328">Actual remaining</text>',
          f'<line x1="{L + 170}" y1="{ly - 4}" x2="{L + 198}" y2="{ly - 4}" stroke="#8c959f" stroke-width="2" stroke-dasharray="6 5"/>',
          f'<text x="{L + 206}" y="{ly}" font-size="12" fill="#1f2328">Ideal burndown</text>', '</svg>']
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sprint", default="Sprint 1")
    ap.add_argument("--owner", default="Adyanth-212", help="GitHub login, or 'all' for the whole team")
    ap.add_argument("--out")
    a = ap.parse_args()
    start, days, issues = load(fetch(), a.sprint, a.owner)
    if not issues:
        raise SystemExit(f"No issues found in {a.sprint} for {a.owner}")
    today = dt.date.today()
    total, actual, ideal = series(issues, start, days, today)
    by = {s: sum(i["pts"] for i in issues if i["status"] == s) for s in ("Done", "In progress", "Todo")}
    who = "whole team" if a.owner == "all" else a.owner
    title = f"{a.sprint} burndown — {who} ({total} pts, {len(issues)} issues)"
    sub = (f"{start.strftime('%-d %b')} – {(start + dt.timedelta(days=days - 1)).strftime('%-d %b %Y')}  ·  "
           f"as of {today.strftime('%-d %b')}: Done {by['Done']} · In progress {by['In progress']} · Todo {by['Todo']} pts")
    slug = a.sprint.lower().replace(" ", "-") + "-" + ("team" if a.owner == "all" else a.owner.split("-")[0].lower())
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{slug}-burndown.svg")
    open(out, "w").write(svg(title, sub, start, days, total, actual, ideal, today) + "\n")
    print(title); print(sub)
    for i in issues:
        print(f"  #{i['n']:<3} {i['pts']} pts  {i['status']:<11} {i['title'][:60]}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
