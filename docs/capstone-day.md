# Capstone day

**The goal.** By 16:00 your team owns a dark factory: a line of agents that turns a GitHub issue
into a tested dbt data product with a dashboard, with nobody in the loop. Then the organisers open
an issue nobody has seen, every team's factory builds it in the same CI pipeline, and an automated
benchmark picks the winner.

You do not start from zero. Every station of the line has a working, deliberately plain baseline
agent, and the repository has a benchmark harness with seed cases. During the day you build up, one
block at a time, the five things the week was about:

| | By the end of the day your team has... | Block |
|---|---|---|
| a | built a custom **[Agno](https://docs.agno.com)** agent that runs a station of the line | 1 |
| b | given it **skills** | 2 |
| c | connected an existing **MCP server**, or written your own | 3 |
| d | written a **benchmark**: cases of your own that pass the validity check | 4 |
| e | used that benchmark to **improve the factory** and can show it with numbers | 5 |

Teams of 2-4. Each team forks the repository and owns the whole line in its fork. The line that
runs in the final is `agents/<station>/` for intake, implement, review, governance and bi.

**Split the team across stations; do not try to improve all of them.** Each person or pair owns one
station and iterates on that station's own benchmark. Stations nobody owns run on their baseline.
Start with **intake, implement, governance and bi**: they map directly onto 80 of the 100 points.
A fifth person takes review (fewer rework rounds, numeric bugs caught before grading). The line
manager is for a team with time to spare.

## What the final is evaluated on

Read these now. They are the questions the automated benchmark asks of your factory's output. The
request itself stays secret until 16:00.

1. **Does it finish on its own?** The line runs from issue to dashboard in CI, without you, within
   45 minutes. Nobody answers questions during the final: when a request is ambiguous but
   buildable, does your factory write down an assumption and deliver, or does it stop?
2. **Does the product have the interface the issue asks for?** The issue names the product id, the
   models, their grain and their columns. Are they all there, under exactly those names?
3. **Are the numbers right, also on checks you have never seen?** Hidden acceptance checks compare
   your models with reference queries on the staging data. Does your factory know Fernhill's
   business rules (cancelled orders, internal QA accounts, currencies, returns) and avoid the
   classic modelling bugs (fan-out joins, averaged ratios, the wrong grain)? Does it test its own
   work before it hands it on?
4. **Does it meet the standards?** Is `checkup` clean for the product (naming, descriptions,
   grain tests, ownership, contracts, layering)?
5. **Is there a dashboard that works?** Does the board validate and render, and does every numbered
   question of the issue have a chart whose query notes say `Answers Q1 - ...`?
6. **What did it cost?** Dollars and minutes for the whole line, counted only as far as the product
   is correct.
7. **Is your own benchmark sound?** Do your new cases score 0 when the agent does nothing and 1 for
   the golden answer?
8. **Does it generalise?** The request is about a part of the warehouse the public products hardly
   use. Did you teach your factory how Fernhill's data works, or how three known products look?

The weights: correctness 50, interface 5, governance 10, dashboard 10, efficiency 15, your own
benchmark 10. Correctness dominates on purpose: a well-governed product with wrong numbers is wrong. The exact formula is in [competition.md](competition.md#scoring-100-points).

## Schedule

| Time | Block | You build | Checkpoint (a facilitator ticks it off) |
|---|---|---|---|
| 09:00 | **Kick-off** (30') | Fork, `uv sync --extra dev`, `factory setup`. Demo of the line on one issue. The rules and the eight questions above. Hand out [interviews.md](interviews.md): what Fernhill's people told you, and what no agent knows yet. | `pytest -q` is green on every laptop. |
| 09:30 | **1 · An Agno agent** (60') | Each person or pair picks a station (see above). Copy `agents/intake-agno/` to `agents/<station>-<team>/`, point it at that station's prompts and outputs, give it the tools it needs. Read the trace of your first run. | `factory run <station> --agent-dir agents/<station>-<team> --case <id>` writes a valid output. A first score from `factory bench run ... --repeat 2` is on your results table, next to the baseline's. |
| 10:30 | Break (15') | | |
| 10:45 | **2 · Skills** (45') | Write one skill from what the traces showed you (Fernhill's business rules, dbt on DuckDB, how to write acceptance checks, dbt charts syntax). Load it with `Skills(loaders=[LocalSkills(...)])`. | The trace shows the agent loading the skill. The results table has a row with and without it. |
| 11:30 | **3 · MCP** (60') | Connect the dbt charts MCP server (`dct mcp serve`), or write your own (a catalogue over `target/manifest.json`, a column profiler, a trace query tool) and connect it with `MCPTools`. | The trace shows a call to an MCP tool. You can say which tool calls it replaced and what that did to score, cost and turns. |
| 12:30 | Lunch (45') | | |
| 13:15 | **4 · A benchmark** (60') | Add at least three cases for your station: one adversarial, one clean control. Take them from failures you saw this morning. Then measure the whole line once: a practice run of the final on a public product. | `factory ci check-cases --out cases.json benchmark/cases/<station>/<yours>.yaml` reports them valid. The baseline line score of a practice run is on your table. |
| 14:15 | **5 · Improve the factory** (90') | Promote your agents to `agents/<station>/`, then go where the practice score says the points are. Each owner iterates on their own station benchmark; a full practice run in CI only checks integration (budget for two or three, not more). | At least two measured changes on the table, one of which you reverted. One green practice run of `competition.yml`. |
| 15:45 | **Freeze** (15') | Open a pull request from your fork to the organisers' repository. Title: your team name in capitals. | The PR is open. Its head commit is what runs. |
| 16:00 | **Final challenge** (45') | The organisers open the issue and start the pipeline for every team. You watch. Meanwhile, prepare a three-minute story. | |
| 16:45 | **Results and demos** (30') | Leaderboard. Per team: the change that mattered most, one thing that did not work, and how well your benchmark predicted your final score. | |
| 17:15 | Retro (15') | What generalised, what overfitted, what you would automate next. | |

### Block notes

**Block 1.** An Agno agent is an agent directory with an `agent.py` that returns an Agno `Agent`
([agents/README.md](../agents/README.md#agno-agents)). The factory runs it like any other station:
same workspace, same trace, same benchmark. The baselines are built with the Claude Agent SDK and
stay in place for the stations you do not rebuild. Start with a station that writes one file
(intake, governance, bi) unless you want the hard one (implement). The track briefs in
[tracks/](tracks/) describe each station and where its baseline is weak.

**Blocks 2 and 3.** Keep both versions of the agent directory so you can compare them:
`factory bench run <station> --agent-dir agents/<x> --label skill-v1 --repeat 3`, then
`factory bench report`. A skill or a tool that does not move score, cost or turns is context you
pay for on every run.

**Key enabler: a shared semantic model.** A dark factory only works when every station means
the same thing by "revenue" or "customer". The data shows what happened; how Fernhill *counts* it
lives in people's heads, in your [interview notes](interviews.md). The baseline agents never see
those notes, and the final is mostly graded on them. Agents are good at finding traps that are
visible in the data; they cannot guess a finance rule. [Apache Ossie](https://ossie.apache.org/) (incubating, formerly Open Semantic Interchange)
is the vendor-neutral YAML standard for metrics, dimensions and their relationships, backed by
dbt, Snowflake, Databricks and others. A team that writes Fernhill's core metrics as an Ossie
model in block 2 (as a skill) or serves it in block 3 (as an MCP tool) gives intake, implement,
governance and bi one source of truth, and it carries over to the hidden product. Its sibling is
[ODCS](https://bitol-io.github.io/open-data-contract-standard/), the Open Data Contract Standard:
Ossie says what the numbers *mean*, an ODCS contract says what the product *guarantees* (schema,
grain, quality rules, owner). Intake writing an ODCS contract that implement and governance check
against is the same idea one station later; the interface section of the final issue is a contract
in all but name. Facilitators: point every team at these by 11:30.

**Block 4.** Your cases, and every file they need (an issue, an overlay with a planted bug), live
under `benchmark/cases/`. Paths in a case resolve relative to the case file first. Cases build on
the public products in `benchmark/products/`. See [benchmark.md](benchmark.md). The practice run is
the end-to-end benchmark: the same workflow and the same scoring as the final, with a public
product as the oracle. Run it in your fork (Actions → *competition · final challenge*, with your
fork, a commit SHA and `oracle: marketing_performance`) or on your laptop
([competition.md](competition.md#trying-it-locally)).

**Block 5.** Station benchmarks are fast and cheap, a practice run is slow and expensive. Use the
first to iterate and the second to check that a better station makes a better product. A practice
run costs real money: agree on a budget per team in the morning.

## The final challenge

- The request is a GitHub issue in the organisers' repository. It describes the need and ends with
  an *Interface* section: the product id, the models and columns to deliver, and the numbered
  questions the dashboard answers.
- Your factory runs in the organisers' CI pipeline (`.github/workflows/competition.yml`), at the
  commit of your pull request at the freeze. From your fork it takes `agents/` and
  `benchmark/cases/`. Everything else is the organisers' code: the runner, the line, the warehouse,
  the standards, the graders, the dependencies and the pipeline. Changes you made to those in your
  fork are not there in the final.
- The line is `factory e2e`: intake → implement → review and governance → rework rounds (as many as `agents/line.yaml` allows) →
  bi. If intake does not return a `ready` spec, the line stops and there is no product.
- One run, 45 minutes, on an API key with a spend limit. No reruns for bad luck.
- The score is computed by the pipeline and posted on your pull request.

## Rules

- **Your factory, the organisers' pipeline.** You may change anything under `agents/` and add
  cases under `benchmark/cases/`. Python packages are fixed: if you need one, ask before lunch and
  it is added for everyone.
- **Improve at least (team size - 1) stations, minimum one**, each with a measured gain on its
  station benchmark. At least one of them is your own Agno agent, with a skill and an MCP server
  in use. A line of untouched baselines does not qualify for the podium.
- **No golden answers in the agent's context.** No copies of `benchmark/products/*/spec.yaml`,
  golden SQL or golden boards in prompts, skills or tools. Knowledge about Fernhill's data is fine,
  and is exactly what a good skill holds: investigate the warehouse and write it down.
- **No human in the loop.** The agents may not fetch anything that somebody wrote after the issue
  was opened. Facilitators read the diff of the winning teams.
- **Measure before you claim.** One run proves nothing. Agents are noisy: repeat, and look at the
  spread.

## For facilitators

Preparation, secrets, the hidden oracle, the freeze-and-reveal commands and the loopholes are in
[competition.md](competition.md). On the day:

- Before 09:00: the baseline's station scores and its practice-run score, cost and duration are on
  the board. They depend on the model, so they are not in the repository.
- Tick off the checkpoints per team. Requirements a-c are checked by you, not by the pipeline.
  A team that is behind at 11:30 connects `dct mcp serve` (ten minutes) and moves on.
- Aim for every station to be rebuilt by at least one team. It makes the retro better.
- Pull requests from forks need a maintainer's approval before the repository's own checks
  (`ci.yml`) run on them.
- The default model is `claude-haiku-5-5`, on purpose: the baseline line should show how the factory
  works and still leave most of the points on the table. An `agent.yaml` can set its own model
  (`model: claude-opus-5-5`); that is a lever, and the cheapest one, so expect every team to try it.
  Do not set `FACTORY_MODEL` for the final: it overrides only `model: default`, but it would make
  the baseline line a moving target. Costs are recorded per run, and Agno runs are priced from token counts
  (`factory/tracing.py`): a model that is not in that table has no cost and scores zero on cost.
