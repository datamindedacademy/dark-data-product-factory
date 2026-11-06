# Capstone day plan (facilitators)

**Goal of the day.** Each team owns one station of the factory line. They measure the
baseline agent on the benchmark, extend the benchmark with cases of their own, and
improve the agent through context engineering. At the end the stations are plugged
into one line and run on a request nobody has seen.

The day uses everything from the week: agents and harnesses (Claude Agent SDK),
context engineering (system prompts, skills, CLAUDE.md, tools), talk-to-your-data
(warehouse tools, SQL), semantic layers (metric definitions in the spec, dbt models
as the interface for BI), and evaluation (the benchmark).

## Design decisions (and why)

**Reference implementations for every station, deliberately plain.** One day is too short
to build an agent harness *and* benchmark it *and* optimise it. Every station therefore
has a working baseline agent (`agents/<station>/`). The baselines have short prompts, no
skills and minimal tools, so there is real headroom. If the baselines were strong,
teams would spend the day on noise.

**Provide the benchmark harness and seed cases; teams extend them.** Designing a
benchmark from scratch takes most of a day by itself. Instead the harness, graders and
3-5 seed cases per station are provided, and every team must add at least three cases
of their own (one of them adversarial). Benchmark design stays a learning goal, but
teams start optimising within the first hour. It also gives a natural conversation
about benchmark validity: "your agent got better on *your* cases - does it on ours?"

**A hold-out set the teams do not see.** Seed cases live in the repo, so teams will
(consciously or not) tune their prompts to them. Facilitators keep a private hold-out
suite (`factory bench run <station> --suite path/to/holdout`) and run it at the end.
The implement benchmark already demonstrates the idea: some acceptance checks are
hidden from the agent.

**Contracts between stations.** Every hand-off is a file with a schema
(`factory/contracts.py`): issue → `spec.yaml` → dbt models → `review.json` /
`governance.json` → board YAML. Teams work in isolation on golden inputs, and the
stations still compose into one line at the end.

**Deterministic graders first, LLM judges as an option.** Scores need to be cheap and
repeatable. Most graders are SQL or schema checks; `--judge` adds rubric-based LLM
judges for what cannot be checked mechanically, and calibrating those is part of the
lesson.

## Before the day

1. `uv sync --extra dev && factory setup && pytest -q` on a clean machine.
2. Decide on API access: one key per team with a spend limit, or the Claude Code login.
   The default model is `claude-opus-5-5` (`FACTORY_MODEL` overrides it). The judge
   model is `claude-sonnet-5-5` (`FACTORY_JUDGE_MODEL`).
3. **Run every baseline once** (`factory bench run <station> --repeat 3`) and write the
   scores and costs on the board. Teams need a reference number at 10:00, and you need to
   know the cost per run to set budgets. These numbers are not in the repo: they depend on
   the model and change with it.
4. Build the hold-out suite (see below) in a private repo.
5. Optional: create a GitHub repo from this one and file the issues in
   `benchmark/products/*/issue.md` with the template in `.github/ISSUE_TEMPLATE/`, so the
   intake team can read real issues (`gh issue view 101 --json title,body`).

### Building a hold-out suite (≈1 hour)

Copy `benchmark/cases/` to a private directory and replace the cases with new ones of
the same shape, for example:

- intake: "basket analysis - which categories are bought together", "store like-for-like
  sales since London opened" (ready), "weather impact on sales" (infeasible).
- implement: write a golden spec + models for one of those under
  `benchmark/products/<id>/` (`spec.yaml` with `matches_reference` checks, `models/`,
  `board.yml`), then reuse it for implement, bi, review and governance cases.
- review / governance: new overlays on the golden products (e.g. a `left join` that
  turns into an `inner join`, a ratio averaged instead of ratio-of-sums, a PII column in
  a fact table).
- line manager: run the generator with another seed and change one planted pattern.

`pytest` style check for your hold-out: `factory bench run <station> --suite <dir> --oracle`
must score 1.0.

## Schedule

| Time | Block | What happens |
|---|---|---|
| 09:00 | Kick-off (30') | The dark factory idea, demo of `factory e2e` on one issue, tour of the repo, the six tracks. |
| 09:30 | Team formation (15') | Teams of 2-4 pick a track. Aim for every station covered once; two teams on one station is fine (they compete). |
| 09:45 | Measure (45') | Run the baseline with `--repeat 3`. Read traces (`runs/**/trace.jsonl`). Write down three hypotheses why it fails. |
| 10:30 | Extend the benchmark (60') | Add ≥3 cases (one adversarial). Check them with `--oracle`. Optional: a new grader or a calibrated judge. |
| 11:30 | Improve, round 1 (60') | One change at a time, measured. Keep a log: change → score, cost, turns. |
| 12:30 | Lunch | |
| 13:15 | Improve, round 2 (105') | Skills, tools, MCP servers, model/effort trade-offs. Variance: `--repeat`. |
| 15:00 | Freeze (15') | Teams hand in their agent directory; facilitators run the hold-out suite. |
| 15:15 | Integration (30') | All stations plugged into one line: `factory e2e --issue <new issue> --agent intake=... --agent bi=...` |
| 15:45 | Demos (60') | 6-8 minutes per team. |
| 16:45 | Retro (15') | What generalised, what overfitted, what you would automate next. |

## Deliverables per team

1. Their agent directory (`agents/<station>-<team>/`) - a copy of the baseline with their changes.
2. Their benchmark cases (`benchmark/cases/<station>/*.yaml` + fixtures), passing `--oracle`.
3. A results table: baseline vs. each significant change, with mean ± stdev over ≥3 repeats,
   cost per run and turns per run (`factory bench report` gives most of it).
4. A demo: one trace that shows the improvement, one thing that did *not* work, and one
   honest statement about how far their benchmark can be trusted.

## Scoring (suggested)

| Component | Weight | How |
|---|---|---|
| Hold-out score improvement over baseline | 40% | `factory bench run <station> --suite holdout --repeat 3`, relative to the baseline score on the same suite |
| Benchmark contribution | 20% | Quality of new cases: do they catch a real failure mode? Is the adversarial case adversarial? |
| Efficiency | 15% | Cost and turns per run at equal or better score. A cheaper model with a better skill can win this. |
| Integration | 10% | The agent works unmodified in the end-to-end line. |
| Demo & insight | 15% | Clear explanation of what changed in the context and why it worked. |

Comparing teams on different stations by raw score is meaningless: compare
*improvement over baseline on the hold-out*.

## Rules of the game

- Change the agent, not the grader. Teams may add cases and graders, but the seed cases
  and the hold-out are fixed.
- No golden answers in the agent's context (no copying `benchmark/products/*/spec.yaml`
  or golden SQL into prompts or skills). General knowledge about Fernhill's data is fine:
  that is exactly what a good skill or CLAUDE.md contains. Facilitators check diffs.
- Measure before you claim: one run proves nothing; LLM agents are noisy.
