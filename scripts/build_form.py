"""Generate the GitHub issue form (.github/ISSUE_TEMPLATE/survey.yml) from survey.yml.

Run after editing survey.yml (the build-form workflow does this on push):
    python scripts/build_form.py
"""

import datetime
import json
import math
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "survey.yml"
LABEL = "survey"


def q(text):
    """JSON strings are valid YAML scalars, so json.dumps quotes safely without a YAML emitter."""
    return json.dumps(str(text), ensure_ascii=False)


def minutes(survey):
    """Honest time estimate: questions × seconds per question, rounded up."""
    questions = len(survey["practices"]) + len(survey.get("context", []))
    return max(1, math.ceil(questions * survey.get("seconds_per_question", 10) / 60))


def when_results_open(survey):
    closes = survey.get("closes_on")
    if not closes:
        return "Results open once everyone has answered."
    if isinstance(closes, str):
        closes = datetime.date.fromisoformat(closes)
    day = f"{closes.day} {closes.strftime('%B %Y')}"
    if survey.get("team_size"):
        return f"Results open on {day}, or earlier once all {survey['team_size']} people have answered."
    return f"Results open on {day}."


def build(survey):
    scale = [option["label"] for option in survey["scale"]]
    header = f"**Takes about {minutes(survey)} minutes.** {when_results_open(survey)}"
    lines = [
        f"name: {q(survey['title'])}",
        f"description: {q('One answer per person. You can edit your issue later to update your answers.')}",
        f"title: {q('Survey answers')}",
        f"labels: [{q(LABEL)}]",
        "body:",
        "  - type: markdown",
        "    attributes:",
        f"      value: {q(header + chr(10) + chr(10) + survey['intro'].strip())}",
    ]
    for item in survey.get("context", []):
        lines += [
            "  - type: dropdown",
            f"    id: {q('context-' + item['id'])}",
            "    attributes:",
            f"      label: {q(item['label'])}",
            f"      options: [{', '.join(q(o) for o in item['options'])}]",
            "    validations:",
            "      required: true",
        ]
    current_stage = None
    for practice in survey["practices"]:
        if practice["stage"] != current_stage:
            current_stage = practice["stage"]
            lines += ["  - type: markdown", "    attributes:", f"      value: {q('### ' + current_stage)}"]
        lines += [
            "  - type: dropdown",
            f"    id: {q(practice['id'])}",
            "    attributes:",
            f"      label: {q(practice['title'])}",
            f"      description: {q(practice['definition'])}",
            f"      options: [{', '.join(q(o) for o in scale)}]",
            "    validations:",
            "      required: true",
        ]
    return "# Generated from survey.yml by scripts/build_form.py. Edit survey.yml, not this file.\n" + "\n".join(lines) + "\n"


def main():
    survey = yaml.safe_load((ROOT / "survey.yml").read_text())
    titles = [p["title"] for p in survey["practices"]]
    if len(set(titles)) != len(titles):
        sys.exit("Practice titles must be unique: the report matches answers by title.")
    FORM.parent.mkdir(parents=True, exist_ok=True)
    FORM.write_text(build(survey))
    print(f"Wrote {FORM.relative_to(ROOT)} with {len(survey['practices'])} practices")


if __name__ == "__main__":
    main()
