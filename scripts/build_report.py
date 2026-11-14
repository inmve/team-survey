"""Build REPORT.md and report/answers.svg from the survey issues.

Usage (the report workflow runs this):
    gh issue list --label survey --state all --limit 1000 \
        --json number,author,body,createdAt,updatedAt > issues.json
    python scripts/build_report.py survey.yml issues.json

One answer per person: the most recently updated issue of each author counts.
The full five-answer distribution is shown for every practice; the Adopt / Trial / Assess / Hold
grouping is a summary of that distribution by a fixed rule, printed in the report.
"""

import datetime
import json
import pathlib
import sys
from collections import Counter, defaultdict

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
NO_RESPONSE = "_No response_"
COLORS = {  # never heard → using, from neutral to strong
    "never_heard": "#d0d7de",
    "not_interested": "#8c959f",
    "want_to_try": "#54aeff",
    "dropped": "#ff8182",
    "using": "#2da44e",
}


def parse_issue_body(body):
    """GitHub renders an issue form as '### <label>' followed by the answer."""
    answers, label, lines = {}, None, []
    for line in (body or "").splitlines():
        if line.startswith("### "):
            if label is not None:
                answers[label] = "\n".join(lines).strip()
            label, lines = line[4:].strip(), []
        elif label is not None:
            lines.append(line)
    if label is not None:
        answers[label] = "\n".join(lines).strip()
    return answers


def latest_per_author(issues):
    latest = {}
    for issue in issues:
        author = (issue.get("author") or {}).get("login") or "unknown"
        if author not in latest or issue["updatedAt"] > latest[author]["updatedAt"]:
            latest[author] = issue
    return latest


def collect(survey, issues):
    scale_by_label = {s["label"]: s["id"] for s in survey["scale"]}
    context_by_label = {c["label"]: c["id"] for c in survey.get("context", [])}
    counts = {p["id"]: Counter() for p in survey["practices"]}
    people = {p["id"]: defaultdict(list) for p in survey["practices"]}
    context = {c["id"]: Counter() for c in survey.get("context", [])}
    respondents = latest_per_author(issues)
    for author, issue in sorted(respondents.items()):
        answers = parse_issue_body(issue.get("body"))
        for practice in survey["practices"]:
            answer = answers.get(practice["title"])
            if answer and answer != NO_RESPONSE and answer in scale_by_label:
                choice = scale_by_label[answer]
                counts[practice["id"]][choice] += 1
                people[practice["id"]][choice].append(author)
        for label, cid in context_by_label.items():
            value = answers.get(label)
            if value and value != NO_RESPONSE:
                context[cid][value] += 1
    return respondents, counts, people, context


def group(c, rules):
    total = sum(c.values())
    if total < rules["min_answers"]:
        return "Not enough answers"
    share = {k: v / total for k, v in c.items()}
    heard = 1 - share.get("never_heard", 0)
    if share.get("using", 0) >= rules["adopt_using"]:
        return "Adopt"
    if share.get("dropped", 0) >= rules["hold_dropped"]:
        return "Hold"
    if share.get("using", 0) + share.get("want_to_try", 0) >= rules["trial_interest"]:
        return "Trial"
    if heard >= rules["assess_heard"]:
        return "Assess"
    return "New to the team"


def svg_chart(survey, counts):
    """Stacked bar per practice: all five answers, same order as the scale, legend on top."""
    row, label_w, bar_w = 26, 330, 420
    width = label_w + bar_w + 50
    legend, x, y = [], 10, 18
    for s in survey["scale"]:
        item_w = 18 + 6.4 * len(s["label"]) + 18
        if x + item_w > width - 10:
            x, y = 10, y + 18
        legend.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" fill="{COLORS.get(s["id"], "#999")}"/>'
                      f'<text x="{x + 15}" y="{y}" fill="#57606a" font-size="11">{s["label"]}</text>')
        x += item_w
    top = y + 18
    height = top + row * len(survey["practices"]) + 12
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="12">',
             '<rect width="100%" height="100%" fill="#ffffff"/>'] + legend
    dark_text = {"never_heard"}  # light segments get dark numbers
    for i, p in enumerate(survey["practices"]):
        y = top + i * row
        c, total = counts[p["id"]], sum(counts[p["id"]].values())
        parts.append(f'<text x="{label_w - 10}" y="{y + 15}" text-anchor="end" fill="#24292f">{p["title"]}</text>')
        x = label_w
        for s in survey["scale"]:
            n = c.get(s["id"], 0)
            if total and n:
                w = bar_w * n / total
                parts.append(f'<rect x="{x:.1f}" y="{y + 4}" width="{w:.1f}" height="16" fill="{COLORS.get(s["id"], "#999")}">'
                             f'<title>{s["label"]}: {n}</title></rect>')
                if w > 16:
                    color = "#24292f" if s["id"] in dark_text else "#ffffff"
                    parts.append(f'<text x="{x + w / 2:.1f}" y="{y + 16}" text-anchor="middle" fill="{color}" font-size="10">{n}</text>')
                x += w
        parts.append(f'<text x="{label_w + bar_w + 8}" y="{y + 15}" fill="#57606a">{total}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def results_open(survey, respondents, today):
    """Results stay closed while the survey runs, so early answers do not steer later ones.
    They open on closes_on, or earlier once team_size people have answered."""
    team_size = survey.get("team_size")
    if team_size and respondents >= team_size:
        return True
    closes = survey.get("closes_on")
    if not closes:
        return not team_size  # no date and no team size: nothing to wait for
    return today >= str(closes)


def closed_report(survey, respondents, today):
    team_size = survey.get("team_size")
    answered = f"{respondents} of {team_size} people have answered" if team_size else f"{respondents} people have answered"
    opens = f"on {survey['closes_on']}" if survey.get("closes_on") else "once everyone has answered"
    if survey.get("closes_on") and team_size:
        opens += f", or earlier once all {team_size} have answered"
    md = "\n".join([f"# {survey['title']}", "",
                    f"**{answered}.** Results open {opens}.", "",
                    "Until then this report shows only the number of answers, so that early answers do not steer later ones.",
                    "Answers themselves are issues in this repository and visible to the team: please answer before reading other people's issues.",
                    "", f"Updated {today}.", ""])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="60" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="14">'
           f'<rect width="100%" height="100%" fill="#ffffff"/><text x="12" y="35" fill="#57606a">{answered}. Results open {opens}.</text></svg>\n')
    return md, svg


def build_report(survey, issues, today=None):
    today = today or datetime.date.today().isoformat()
    respondents, counts, people, context = collect(survey, issues)
    if not results_open(survey, len(respondents), today):
        return closed_report(survey, len(respondents), today)
    rules = survey["report"]
    scale = survey["scale"]
    md = [f"# {survey['title']}", "",
          f"Report of {today} · {len(respondents)} people answered · survey version {survey['version']}.",
          "Answers are visible to everyone with access to this repository; this report only sums them up.", "",
          "![All answers per practice](report/answers.svg)", ""]

    groups = defaultdict(list)
    for p in survey["practices"]:
        groups[group(counts[p["id"]], rules)].append(p["title"])
    md += ["## Team radar", ""]
    for name in ["Adopt", "Trial", "Assess", "Hold", "New to the team", "Not enough answers"]:
        if groups.get(name):
            md.append(f"- **{name}:** " + ", ".join(groups[name]))
    md += ["", f"Rule: a practice is grouped only with at least {rules['min_answers']} answers. "
               f"Adopt: at least {rules['adopt_using']:.0%} use it and will keep using. "
               f"Hold: at least {rules['hold_dropped']:.0%} tried it and would not use again. "
               f"Trial: using + want to try is at least {rules['trial_interest']:.0%}. "
               f"Assess: at least {rules['assess_heard']:.0%} have heard of it. Otherwise: new to the team.", ""]

    split = [p for p in survey["practices"] if sum(counts[p["id"]].values()) >= rules["min_answers"]
             and counts[p["id"]].get("using", 0) / sum(counts[p["id"]].values()) >= rules["split_share"]
             and counts[p["id"]].get("never_heard", 0) / sum(counts[p["id"]].values()) >= rules["split_share"]]
    md += ["## Where the team splits", "",
           f"Practices that at least {rules['split_share']:.0%} use and at least {rules['split_share']:.0%} have never heard of: "
           "knowledge that is not spreading inside the team.", ""]
    md += [f"- **{p['title']}**: ask {', '.join('@' + a for a in people[p['id']]['using'])}" for p in split] or ["- none"]
    md.append("")

    want = sorted((p for p in survey["practices"] if counts[p["id"]].get("want_to_try")),
                  key=lambda p: -counts[p["id"]]["want_to_try"])
    md += ["## What people want to try", ""]
    for p in want:
        users = people[p["id"]]["using"]
        md.append(f"- **{p['title']}** ({counts[p['id']]['want_to_try']}): {p['definition']}"
                  + (f" Already using it: {', '.join('@' + a for a in users)}." if users else ""))
    if not want:
        md.append("- none")
    md.append("")

    md += ["## All answers", "",
           "| Stage | Practice | " + " | ".join(s["label"] for s in scale) + " | Total |",
           "|---|---|" + "---:|" * (len(scale) + 1)]
    for p in survey["practices"]:
        c = counts[p["id"]]
        md.append(f"| {p['stage']} | {p['title']} | " + " | ".join(str(c.get(s['id'], 0)) for s in scale) + f" | {sum(c.values())} |")
    md.append("")

    md += ["## Who answered", ""]
    for item in survey.get("context", []):
        c = context[item["id"]]
        md.append(f"- **{item['label']}:** " + (", ".join(f"{opt} {c[opt]}" for opt in item["options"] if c.get(opt)) or "no answers"))
    md += ["", "Generated by scripts/build_report.py from the issues labelled `survey`. "
               "Run the survey again later: people edit their issue, and the git history of this file shows how the team changed.", ""]
    return "\n".join(md), svg_chart(survey, counts)


def main():
    survey_path = sys.argv[1] if len(sys.argv) > 1 else "survey.yml"
    issues_path = sys.argv[2] if len(sys.argv) > 2 else "issues.json"
    survey = yaml.safe_load((ROOT / survey_path).read_text())
    issues = json.loads((ROOT / issues_path).read_text())
    report, svg = build_report(survey, issues)
    (ROOT / "REPORT.md").write_text(report)
    (ROOT / "report").mkdir(exist_ok=True)
    (ROOT / "report" / "answers.svg").write_text(svg)
    print(f"REPORT.md written from {len(issues)} issues")


if __name__ == "__main__":
    main()
