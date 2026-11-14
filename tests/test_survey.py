"""Tests for the form generator and the report builder.

Run: python -m unittest discover tests
The fixture tests/fixtures/issues.json is made-up test data in the shape `gh issue list --json` returns.
"""

import copy
import json
import pathlib
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_form  # noqa: E402
import build_report  # noqa: E402

SURVEY = yaml.safe_load((ROOT / "survey.yml").read_text())
ISSUES = json.loads((ROOT / "tests" / "fixtures" / "issues.json").read_text())


class FormTest(unittest.TestCase):
    def test_form_is_valid_yaml_with_one_required_dropdown_per_practice_and_context_question(self):
        form = yaml.safe_load(build_form.build(SURVEY))
        dropdowns = [item for item in form["body"] if item["type"] == "dropdown"]
        self.assertEqual(len(dropdowns), len(SURVEY["practices"]) + len(SURVEY["context"]))
        self.assertTrue(all(d["validations"]["required"] for d in dropdowns))
        self.assertEqual(form["labels"], ["survey"])

    def test_form_states_the_time_and_when_results_open(self):
        form = yaml.safe_load(build_form.build(SURVEY))
        intro = form["body"][0]["attributes"]["value"]
        self.assertIn("Takes about 4 minutes", intro)  # 20 questions × 10 s, rounded up
        self.assertIn("Results open on 1 December 2026, or earlier once all 12 people have answered", intro)

    def test_practice_dropdowns_offer_the_five_answer_scale(self):
        form = yaml.safe_load(build_form.build(SURVEY))
        practice = next(d for d in form["body"] if d.get("id") == "worktree")
        self.assertEqual(practice["attributes"]["options"], [s["label"] for s in SURVEY["scale"]])


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.respondents, self.counts, self.people, self.context = build_report.collect(SURVEY, ISSUES)

    def test_counts_only_the_latest_issue_of_each_author(self):
        self.assertEqual(len(self.respondents), 4)
        # alice first answered "never heard" for vibe coding, then edited it to "dropped": only the later answer counts
        self.assertEqual(self.counts["vibe-coding"]["never_heard"], 0)
        self.assertEqual(self.counts["vibe-coding"]["dropped"], 2)  # alice (latest) and carol

    def test_keeps_all_five_answers_per_practice(self):
        c = self.counts["plan-first-before-coding"]
        self.assertEqual(sum(c.values()), 4)
        self.assertEqual(c["using"], 3)
        self.assertEqual(c["want_to_try"], 1)

    def test_groups_practice_used_by_half_the_team_as_adopt(self):
        self.assertEqual(build_report.group(self.counts["plan-first-before-coding"], SURVEY["report"]), "Adopt")

    def test_does_not_group_with_fewer_answers_than_the_minimum(self):
        self.assertEqual(build_report.group({"using": 2}, SURVEY["report"]), "Not enough answers")

    def test_hides_results_before_the_closing_date(self):
        report, svg = build_report.build_report(SURVEY, ISSUES, today="2026-11-14")
        self.assertIn("4 of 12 people have answered", report)
        self.assertNotIn("## Team radar", report)
        self.assertNotIn("@bob", report)

    def test_opens_results_on_the_closing_date(self):
        report, _ = build_report.build_report(SURVEY, ISSUES, today="2026-12-01")
        self.assertIn("## Team radar", report)

    def test_opens_results_early_when_the_whole_team_answered(self):
        survey = copy.deepcopy(SURVEY)
        survey["team_size"] = 4
        report, _ = build_report.build_report(survey, ISSUES, today="2026-11-14")
        self.assertIn("## Team radar", report)

    def test_report_lists_who_uses_a_split_practice(self):
        report, svg = build_report.build_report(SURVEY, ISSUES, today="2026-12-02")
        self.assertIn("## Where the team splits", report)
        self.assertIn("One git worktree per agent**: ask @bob, @carol", report)
        self.assertIn("4 people answered", report)
        self.assertTrue(svg.startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
