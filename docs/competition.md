# The final (organisers)

On Friday the organisers open one GitHub issue with a request nobody has seen. Every team's factory
answers it, unattended, in a CI pipeline the team cannot change. The answers are scored against the
right answers, which only the organisers have. Highest score wins.

Participants read [capstone-day.md](capstone-day.md). This page is the design, the runbook and the
loopholes that remain.

## Design

```
 team fork ── PR ──▶ organisers' repo                          private oracle repo
 (agents/, benchmark/cases/)   │                                 products/<id>/issue.md, answers.json
                               ▼  competition.yml (workflow_dispatch, organisers only)
   run    API key · team code          checkout = organisers' main, agents/ from the frozen commit
          factory line --issue <the issue>   ─▶ artifact submission/ (answers.json, run summaries)
   grade  right answers · no team code ─▶ score.json, score.md (step summary, PR comment)
          checks the team's new cases, reads JSON only
```

**Teams cannot change the grading.** The score only comes from `competition.yml` in the organisers'
repository, dispatched by an organiser. It checks out the organisers' code and takes two folders from
the team's commit: `agents/` (their factory) and `benchmark/cases/` (their cases, data files only).
The base agent, the line, the graders, the data and the dependencies are never theirs.

**Running and grading are separate jobs.** The run job has the API key and no right answers. The
grade job has the right answers and runs no team code: it only reads `answers.json` and the run
summaries.

**Freeze, then reveal.** Teams open a PR to the organisers' repo before the freeze. The organisers
record each PR's head commit, open the issue, then dispatch the workflow with the recorded commit.

**The request fixes the format.** It ends with an *Answers* section: a JSON template with every
question and key. What stays hidden is what makes the numbers right: the business rules and the
traps in the data.

## Scoring (100 points)

In [`factory/competition.py`](../factory/competition.py), tested in `tests/test_line.py`.

| Component | Points | How it is measured |
|---|---:|---|
| Correctness | 70 | Per question, the share of its values within 0.5% of the right answer; the mean over the questions |
| Efficiency | 15 | Correctness × the mean of a cost score and a time score, linear between full marks and zero (`COST_USD`, `DURATION_S`). Time from GitHub, cost from the team's own OpenRouter key |
| Own benchmark | 15 | New, valid cases under `benchmark/cases/` (doing nothing scores 0, the right answer scores 1); 3 = full marks |

Ties: lower cost, then shorter duration.

## Make it hard: hidden know-how

A capable model finds the traps that are visible in the data on its own: duplicate loads, cancelled
orders, currencies. It can't find rules that exist only in people's heads. The interview recording has those, handed
out at the kick-off; [interviews.md](interviews.md) only has the org chart and the headlines. Its
teleprompt script and Slidev deck are in the oracle repo (`interviews/`): the script is the full
transcript, so it stays private. Render it before the day (`teleprompt build scripts/interviews.md`,
with a speech server) and share the video, not the script. Most of the final's answers
depend on them.

Measured on 2026-11-27 on the final, three runs each with the Gemma baseline line: 4, 0 and 0 out of
100, $0.02 to $0.14 and 1 to 5 minutes a run. With the interview notes pasted into every agent's
instructions and nothing else changed: 34, 69 and 26. After the notes were rewritten to leave out the
data codes (status values, the test domain, dates), five runs: 64, 2, 14, 28 and 65. The notes are
worth a lot, which is the intent, but pasting them in is not enough for a steady score. The scales: full cost marks up to $0.035 and zero from
$0.21 (half and three times the baseline); full time marks up to 3 minutes and zero from 15. The time
scale is a guess from local runs plus CI setup: check it on the first CI run of the baseline.

## Runbook

### Weeks before

1. Publish this repository as the organisers' repo. Teams fork it.
2. Secrets: `LLM_API_KEY_<TEAM>` per team (team name in capitals): a fresh OpenRouter key with a
   spend limit, used for nothing but that team's final run. The grade job reads the key's spend as
   the run's cost, so never practise with it. `LLM_API_KEY` for practice runs. `ORACLE_TOKEN`: a
   read-only token for the private oracle repo; variable `ORACLE_REPO` (`owner/name`).
3. The oracle in the private repo: `products/<id>/issue.md` and `answers.json`, like the practice
   requests in `benchmark/products/`, and the script that computes the answers. The practice requests'
   scripts live there too (`products/practice/`): they spell out every rule, so they stay out of the
   factory repo.
4. Calibrate: dispatch `competition.yml` with the baseline agents on a practice request
   (`oracle: category_performance`, no issue). Set `COST_USD` and `DURATION_S` from it.

### On the day

```bash
# Freeze: one open PR per team, PR title = team name (A-Z, 0-9, _)
gh pr list --json number,title,headRefOid,headRepositoryOwner,headRepository > freeze.json

# Reveal
ISSUE=$(gh issue create --title "<the title in issue.md>" --body-file products/$ID/issue.md | grep -o '[0-9]*$')

# Run every team at its frozen commit
jq -r '.[] | [.title, "\(.headRepositoryOwner.login)/\(.headRepository.name)", .headRefOid, .number] | @tsv' freeze.json |
while IFS=$'\t' read -r team repo sha pr; do
  gh workflow run competition.yml -f team="$team" -f repo="$repo" -f sha="$sha" -f oracle="$ID" -f issue="$ISSUE" -f pr="$pr"
done

# Leaderboard
mkdir scores && cd scores && gh run list --workflow competition.yml --limit 30 --json databaseId --jq '.[].databaseId' |
  xargs -I{} gh run download {} --pattern 'score-*' --dir {} 2>/dev/null
jq -s 'sort_by(-.total) | .[] | "\(.total)\t$\(.cost_usd)\t\(.duration_s)s"' -r */*/score.json
```

Before announcing a winner, read the diff of the top teams' `agents/` folder.

## Loopholes that remain

- **The run job gives team code the API key.** Per-team keys with a spend limit, revoked after the
  event, bound the damage. The right answers are not in that job.
- **A human in the loop.** The run job has open network access, so code committed before the freeze
  could fetch answers written after the reveal. The freeze makes that deliberate fraud, visible in the
  diff; only a runner with an egress allowlist would prevent it.
- **One run per team.** Agents are noisy. Dispatch each team three times and take the median if the
  budget allows.
- **The benchmark points measure validity, not usefulness.** Three trivial but valid cases earn full
  marks. Judge usefulness in the demos if it matters.
- **The right answers leak slowly.** The score table shows the score per question. Use a new request
  for a second round.

## Trying it locally

```bash
factory line --issue benchmark/products/marketing_performance/issue.md
factory score runs/<the line run>
```
