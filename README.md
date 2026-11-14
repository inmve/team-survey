# State of Agentic Practices: team survey

A ready-made survey for your engineering team: which agentic coding practices people use, want to try, tried and dropped, or never heard of. Answers are GitHub issues in your own private repository; a GitHub Action turns them into a report.

- 18 practices from planning to review, each with a one-line definition. Takes about 4 minutes.
- One question per practice, five answers, the same scale as the State of JS survey.
- The report shows every answer, plus a team radar, the practices where the team splits, and what people want to try.

**Answers are visible to the team.** Anyone with access to the repository sees who answered what. The report names who already uses a practice, so others know whom to ask.

**Results stay closed while the survey runs.** Until the closing date, or until everyone has answered, `REPORT.md` shows only how many people answered. Seeing that "everyone uses X" changes how people answer, so nobody sees the results early. The answers themselves are issues, so ask people to answer before reading others' issues.

## Run it in 5 minutes

1. Click **Use this template → Create a new repository**. Choose your organization as the owner and **Private** as the visibility.
2. In the new repository: **Settings → Actions → General → Workflow permissions → Read and write permissions** → Save. The workflows need this to commit the report.
   Then open **Actions → Build survey form → Run workflow** once. It creates the `survey` label (a repository made from a template does not get the template's labels, and the report finds answers by this label).
3. Edit `survey.yml`: set `closes_on` (when results open) and `team_size` (results open earlier once that many people answered). Optional: remove practices you don't care about, add your own (id, stage, title, definition). On push, a workflow rebuilds the form, including the time estimate at the top.
4. Send the team this link: `https://github.com/<owner>/<repo>/issues/new?template=survey.yml`
5. Open `REPORT.md`. It is rebuilt after every answer and once a day; it shows the full results from the closing date.

Run it again in a quarter: ask people to edit their issue. Only the latest answer of each person counts, and the git history of `REPORT.md` shows how the team changed.

## The answer scale

| Answer | Means |
|---|---|
| Never heard of it | the practice has not reached this person |
| Heard of it, not interested | knows it, sees no reason to try |
| Heard of it, want to try | interest without experience: a candidate for a team session |
| Tried it, would not use again | tried and dropped |
| Use it, will keep using | part of how this person works |

## How the report groups practices

The report always shows the full distribution of the five answers. On top of that it groups practices into a team radar by a fixed rule, written in the report and set in `survey.yml` under `report`:

- Adopt: at least 50% use it and will keep using.
- Hold: at least 25% tried it and would not use it again.
- Trial: using + want to try is at least 50%.
- Assess: at least 50% have heard of it.
- A practice is grouped only with at least 3 answers.

## Files

| File | What it is |
|---|---|
| `survey.yml` | the practices, the scale, context questions, report thresholds |
| `.github/ISSUE_TEMPLATE/survey.yml` | the form, generated from `survey.yml`; don't edit by hand |
| `.github/workflows/build-form.yml` | rebuilds the form when `survey.yml` changes |
| `.github/workflows/report.yml` | rebuilds `REPORT.md` and `report/answers.svg` after every answer |
| `scripts/` | the form and report builders (Python, needs `pyyaml`) |
| `tests/` | tests on made-up data: `python -m unittest discover tests` |

## Updating

A repository created from a template does not receive later changes. Compare `version` in your `survey.yml` with this template and copy what you need.

Practices and definitions come from the Agentic Coding Reference on coding-with-ai.dev.
