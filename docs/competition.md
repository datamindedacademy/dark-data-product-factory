# The final challenge (organisers)

At the end of the day the organisers open one GitHub issue with a data product request nobody
has seen. Every team's factory builds it, unattended, in a CI pipeline the team cannot change.
An automated benchmark scores the result. Highest score wins.

Participants read [capstone-day.md](capstone-day.md). This page is the design, the runbook and
the list of loopholes that remain.

## Design

```
 team fork ── PR ──▶ organisers' repo                              private oracle repo
 (agents/, benchmark/cases/)   │                                     products/<id>/spec.yaml
                               ▼  competition.yml (workflow_dispatch, organisers only)
   run    API key · team code     checkout = organisers' main, overlay agents/ from the frozen SHA
          factory e2e --issue <the issue>  ─▶ artifact submission/ (spec, models, board, traces)
   build  no secrets · untrusted SQL only  ─▶ artifact build/ (warehouse.duckdb, build.json, cases.json)
          clean checkout + only .sql/.yml/.md from the submission; dbt build, checkup, dct
   grade  hidden oracle · no team code     ─▶ score.json, score.md (step summary, PR comment)
          reads JSON/YAML, queries the built database read-only
```

**Teams cannot change the grading.** They work in a fork. The score only ever comes from
`competition.yml` in the organisers' repository, dispatched by an organiser. That workflow checks
out the organisers' code and takes exactly two paths from the team's commit: `agents/` (their
factory) and `benchmark/cases/` (their benchmark). The runner, the line, the CLI, the warehouse,
the standards, the graders, the dependencies and the workflow itself are never theirs. Teams run
the same workflow in their fork for practice. Changing it there changes nothing in the final.

**Execution and grading are separate jobs.** The job that runs team code has the API key and no
oracle. The job that has the oracle runs no team code. Between them sits a job with no secrets
that builds the submitted SQL in a clean checkout. Only artifacts cross the boundaries, and each
job treats what it receives as untrusted data: the build job copies only `.sql`, `.yml` and `.md`
files (no dbt Python models), the grade job only parses YAML/JSON and queries a DuckDB file.

**Freeze, then reveal.** Teams open a PR to the organisers' repo before the freeze. The organisers
record each PR's head SHA, then open the issue, then dispatch the workflow with the recorded SHA.
Commits pushed after the reveal are not run.

**The issue fixes the interface.** A hidden check can only query a model it can name, so the issue
ends with an *Interface* section: product id, model names, grain, columns and the numbered
questions. `factory ci final-issue` generates it from the oracle spec, so issue and oracle cannot
drift. What stays hidden is what makes the numbers right: the business rules, the data traps and
the checks themselves.

**The oracle is a golden spec.** Same format as `benchmark/products/*/spec.yaml`. Its `outputs`
are the published interface, its acceptance checks are the hidden checks, its question ids are
what the dashboard must answer. Reference queries run on a pristine warehouse generated in the
grade job, never on the database the team's SQL touched. A model that tampers with the source
data only makes its own numbers wrong.

## Scoring (100 points)

Implemented in [`factory/competition.py`](../factory/competition.py), tested in
`tests/test_competition.py`.

| Component | Points | How it is measured | Trusted? |
|---|---:|---|---|
| Correctness | 50 | Fraction of the oracle's hidden acceptance checks that pass on the built product | yes |
| Interface | 5 | Fraction of the required models and columns that exist | yes |
| Governance | 10 | `checkup` on the product, all rules it can check (GOV-001..010, the judgement ones as heuristics): `max(0, 1 - violations / 5)`; 0 when `dbt build` fails (a model or one of its tests) | yes |
| Dashboard | 10 | One third each: `dct validate`, `dct render`, share of questions answered correctly (`Q1`... in query notes or chart titles of placed charts, *and* all of that question's hidden checks pass) | yes |
| Efficiency | 15 | Correctness × mean of a cost score and a time score. Full marks up to $2 and 10 min, zero from $12 and 45 min, linear in between | time yes, cost self-reported |
| Own benchmark | 10 | New cases under `benchmark/cases/` that are valid (doing nothing scores 0, oracle scores 1); 3 valid cases = full marks | yes |

Efficiency is multiplied by correctness so that a fast factory that builds nothing earns nothing.
Ties: lower cost, then shorter duration. The score table is posted on the team's PR and in the
workflow summary. It names which hidden checks failed, not what they check.

`checkup` scores GOV-006, 008 and 010 with heuristics (`factory/tools/checkup.py`); the agents'
`warehouse/checkup.yaml` does not enable them. GOV-011 (business rules) cannot be checked
generically: put it in the oracle as acceptance checks (an `empty` check for QA accounts), so it
counts under correctness.

### Make the oracle hard: hidden know-how

A capable model finds every trap that is visible in the data (cancelled orders, currencies,
duplicates) on its own. What it cannot find is company know-how: rules that exist only in people's
heads. [interviews.md](interviews.md) is the hand-out with those rules, given to teams at the
kick-off; the baseline agents never see it. Base most of the oracle's checks on them. Measured on
2026-11-22 with the hidden oracle (13 checks, 5 hidden rules): the Haiku baseline
passes the 4 structural checks and fails the 9 that need the rules, about 40 / 100.

## Runbook

### Weeks before

1. Publish this repository as the organisers' repo. Teams get read access only: they fork.
2. Secrets: `ANTHROPIC_API_KEY_<TEAM>` per team (team name in capitals, `A-Z0-9_`), each key with
   a spend limit. `ANTHROPIC_API_KEY` is the fallback. `ORACLE_TOKEN`: read-only token for the
   private oracle repository. Variable `ORACLE_REPO` (`owner/name`), optionally `FACTORY_MODEL`.
3. Write the oracle in the private repo: `products/<id>/issue.md`, `spec.yaml`, `models/`,
   `board.yml`, like a product in `benchmark/products/`. Use tables the public products barely
   touch. Keep column descriptions neutral: they are published in the issue. Check it:

   ```bash
   mkdir -p sub && cp products/<id>/{spec.yaml,board.yml} sub/ && cp -r products/<id>/models sub/models
   factory ci build-submission sub build
   factory ci score sub build --oracle products/<id>/spec.yaml      # 50 / 5 / 10 / 10 expected
   ```

4. Calibrate: dispatch `competition.yml` with the baseline agents on a public product
   (`oracle: category_performance`, no issue). Note score, cost and duration, put them on the
   board on the day, and set `COST_USD` and `DURATION_S` in `factory/competition.py` to roughly
   half and three times the baseline.

### On the day

```bash
# Freeze: one open PR per team, PR title = team name (A-Z, 0-9, _)
gh pr list --json number,title,headRefOid,headRepositoryOwner,headRepository > freeze.json

# Reveal: the issue with the generated interface section
factory ci final-issue --issue products/$ID/issue.md --oracle products/$ID/spec.yaml > body.md
ISSUE=$(gh issue create --title "Data product: ..." --body-file body.md | grep -o '[0-9]*$')

# Run every team at its frozen commit
jq -r '.[] | [.title, "\(.headRepositoryOwner.login)/\(.headRepository.name)", .headRefOid, .number] | @tsv' freeze.json |
while IFS=$'\t' read -r team repo sha pr; do
  gh workflow run competition.yml -f team="$team" -f repo="$repo" -f sha="$sha" -f oracle="$ID" -f issue="$ISSUE" -f pr="$pr"
done

# Leaderboard
mkdir scores && cd scores && gh run list --workflow competition.yml --limit 30 --json databaseId --jq '.[].databaseId' |
  xargs -I{} gh run download {} --pattern 'score-*' --dir {} 2>/dev/null
jq -s 'sort_by(-.total) | .[] | "\(.total)\t\(.team)\t$\(.cost_usd)\t\(.duration_s)s"' -r */*/factory-out/score.json
```

Before announcing a winner: compare the top teams' reported cost with the spend on their API key,
and read the diff of their `agents/` directory.

## Loopholes that remain

- **The run job gives team code the API key.** It can be sent anywhere. Per-team keys with a spend
  limit, revoked after the event, bound the damage. Nothing else in that job is worth stealing: the
  token is read-only and the oracle is not there.
- **A human in the loop.** The run job has open network access. Team code committed before the
  freeze could fetch a hand-made solution written after the reveal. The freeze makes this
  deliberate fraud that is visible in the PR diff, but only a runner with an egress allowlist
  would prevent it.
- **Cost is self-reported.** Traces are written in the job that runs team code, and Agno runs are
  priced from token counts (`factory/tracing.py`). A station without a cost counts as the worst
  cost, but a forged trace is possible. Duration is measured by GitHub and is not forgeable. The
  exposure is 5 points; check the winners against their key's spend.
- **"Built with Agno" is self-reported** for the same reason (`framework` in the traces, shown in
  the score table). Facilitators check it at the block 1 checkpoint and in the diff.
- **Untrusted SQL runs in the build job.** dbt and dbt charts run with DuckDB's external access
  disabled (`warehouse/profiles.yml`), there are no secrets and no Python models are copied. But
  dbt Jinja is expressive. Someone who broke out of that job could forge governance, dashboard and
  benchmark results (30 points), not correctness: the right numbers are only in the oracle.
- **One run per team.** Agents are noisy, so luck can decide a close race. Dispatch each team three
  times and take the median if the budget allows.
- **The benchmark score measures validity, not usefulness.** Three trivial but valid cases earn
  full marks. Judge usefulness in the demos if it matters.
- **The oracle leaks slowly.** Score tables name the failed check ids, and anyone with write access
  to the organisers' repo can dispatch the workflow. Use a new oracle for a second round.
- **Budgets in `agent.yaml` are the team's.** `max_budget_usd` is theirs to edit and Agno does not
  enforce it. The hard limits are the 45-minute step timeout and the key's spend limit.
- **Forks must be readable** by the workflow. For private team repos, add a read token to the two
  `git fetch` steps.

## Trying it locally

The three commands the workflow runs also work on a laptop, with a public product as the oracle:

```bash
P=benchmark/products/marketing_performance
factory ci final-issue --issue $P/issue.md --oracle $P/spec.yaml > issue.md
factory e2e --issue issue.md                      # your line (API credits!)
factory ci export-submission submission
factory ci build-submission submission build
factory ci score submission build --oracle $P/spec.yaml
```
