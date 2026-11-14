# Progress: team-survey (GitHub template for an agentic coding practices survey)

## Current Status
- **Last Updated**: 2026-11-14
- **Status**: Built locally, tests pass; not a git repo yet, not on GitHub
- **Completion**: ~70% (template works on made-up data; not tried on a real GitHub repository)

## Original requests (Ivan, verbatim)
1. "а еще вот что думаю - хочется что б этот тест могли прогнать внутри команд своих --- тут как будто можно иметь какой-то шаблон и что б cto если увидел сайт он мог бы быстро прогнать такой опрос у себя; давай подумаем как сделать"
2. "GitHub-шаблон"
3. "а может ли он форкнуть репо и сделать его приватным сразу?"
4. "давай открыто в команде, делай шаблон"
5. "ну и получается идем по пути state of js со многими вариантами ответа"
6. "и получается надо показывать ответы потом не по is-it-used а для всех; верно?"
7. "и еще по поводу опроса - хорошо бы сделать так что ответы получат только те кто пройдет опрос (и сориентировать по времени сколько опрос будет длиться); логично?" / "Да, делай"

## Decisions
- **Delivery**: GitHub template repository ("Use this template" → private copy in the team's org). A fork of a public repo cannot be made private, so not a fork.
- **Anonymity**: answers are open inside the team (issue author is visible; issue edit history would expose answers even if a workflow redacted them). Stated in the README and in every report.
- **Scale**: State of JS style, five answers per practice: never heard / heard, not interested / heard, want to try / tried, would not use again / use, will keep using.
- **Report shows all five answers** per practice (stacked bar SVG + table), not a used / not used split. Team radar (Adopt / Trial / Assess / Hold) is a summary by a fixed rule printed in the report; thresholds in `survey.yml`.
- **Open team = useful names**: "Where the team splits" and "What people want to try" name who already uses the practice, so people know whom to ask.
- **One answer per person**: the most recently updated issue of each author counts; re-running in a quarter = people edit their issue, git history of REPORT.md is the team trend.
- **Practices**: 18 from the Agentic Coding Reference (`~/Code/ai_stack-reference-glossary`, data/entries.json), definitions shortened to one sentence, titles rewritten as practices.
- **Results closed while the survey runs** (Ivan's ask: only people who answered get results). GitHub cannot show a file to some repo members and hide it from others, so: REPORT.md shows only the answer count until `closes_on`, or earlier once `team_size` people answered; a daily scheduled run opens it on the date. This fully removes anchoring on results; answers themselves stay readable as issues (README asks to answer first).
- **Time estimate**: questions × `seconds_per_question` (10 s), rounded up: 20 questions → about 4 minutes, shown at the top of the form with the date results open.
- **No YAML emitter dependency**: the form generator writes YAML with JSON-quoted strings; PyYAML only for reading `survey.yml` (installed in workflows).

## Timeline
- 2026-11-14: Added closing date, team size and time estimate; closed-results report; daily workflow run; 11 tests pass.
- 2026-11-14: Created `survey.yml`, `scripts/build_form.py`, `scripts/build_report.py`, workflows `build-form.yml` and `report.yml`, README, tests with a made-up fixture (`tests/fixtures/issues.json`, 4 people, one edited answer). 7 tests pass. Sample report and chart checked visually, then removed so the template ships with an empty REPORT.md.

## Current Context
- **What's working**: form generation (18 required dropdowns + 2 context questions), report (radar, splits, want to try, all answers table, who answered, SVG chart), tests.
- **Not verified**: real GitHub run (issue form rendering, `gh issue list` output, workflow commit permissions).
- **What's next**: Ivan picks the repo name; create the GitHub repo (outward action, needs Ivan's go), mark it as a template, run one real answer end to end; then link it from the reference ("Run this in your team").

## Next Steps
- [ ] Name and create the GitHub repository; mark as template
- [ ] End-to-end check on GitHub with one real issue
- [ ] Link from the reference page
- [ ] Later: the same five-answer distribution in the public reference instead of yes/no
