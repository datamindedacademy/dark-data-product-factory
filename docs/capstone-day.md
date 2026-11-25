# Capstone

**The goal.** By Friday 14:00 your team owns a dark factory: a line of agents that turns a GitHub
issue into a tested dbt data product with a dashboard, with nobody in the loop. Then the organisers
open an issue nobody has seen, every team's factory builds it in the same CI pipeline, and an
automated benchmark picks the winner.

You do not start from zero. Every station of the line has a working, deliberately plain baseline
agent, and the repository has a benchmark harness with seed cases. Teams of 2-4. Each team forks
the repository and owns the whole line in its fork. The line that runs in the final is
`agents/<station>/` for intake, implement, review, governance and bi.

**How you work: one agent, the whole loop, then the next.**

1. **Benchmark.** Write a few cases for the agent and score it as it is.
2. **Traces.** Read the traces of the cases that lost points: what went wrong?
3. **Context.** Change one thing: the prompt, a skill, a tool, an MCP server.
4. **Repeat.** Run the benchmark again. Better: keep the change. Worse: undo it.

On **Thursday afternoon** the whole team takes one agent through that loop, the one where the most
points are. On **Friday** you take the same loop to as many other agents as you want. Which agent
comes next is a judgement call; correctness weighs half the final score, so intake and implement
usually pay off most. [agents/README.md](../agents/README.md) has the commands.

## What the final is evaluated on

Read these now. They are the questions the automated benchmark asks of your factory's output. The
request itself stays secret until Friday.

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

Clock times follow from the bootcamp schedule. TODO: fill them in.

| When | Block | You do |
|---|---|---|
| Thursday afternoon | **Kick-off** | Fork, `uv sync --extra dev`, `factory setup` (a Codespace does this for you). Demo of the line on one issue. The rules and the eight questions above. Hand out [interviews.md](interviews.md): what Fernhill's people told you, and what no agent knows yet. |
| Thursday afternoon | **One agent, the whole loop** | Pick the agent with the most points to win. Benchmark it, read its traces, change its context, repeat. Add cases of your own as you find failures: three valid cases are worth 10 points in the final. |
| Friday | **More agents** | The same loop on as many other agents as you want. Check now and then that a better station makes a better product: a practice run of the final on a public product. |
| Friday | **Freeze** | Open a pull request from your fork to the organisers' repository. Title: your team name in capitals. Its head commit is what runs. |
| Friday | **Final challenge** (45') | The organisers open the issue and start the pipeline for every team. You watch, and prepare a three-minute story. |
| Friday, before 14:00 | **Results and retro** | Leaderboard. Per team: the change that mattered most, one thing that did not work, and how well your benchmark predicted your final score. What generalised, what overfitted. |

### Notes

**Benchmark.** `factory bench run <station> --agent-dir agents/<x> --label v1 --repeat 3`, then
`factory bench report`. Your cases, and every file they need (an issue, an overlay with a planted
bug), live under `benchmark/cases/`; see [benchmark.md](benchmark.md). `factory ci check-cases
--out cases.json <case.yaml>` checks that a case is valid (doing nothing scores 0, the golden answer
scores 1).

**Traces.** Every run writes `trace.jsonl` and `summary.json` under `runs/`. With Phoenix running
(`make phoenix`, or automatically in a Codespace) every run is also a trace at
http://localhost:6006.

**Context.** Anything that moves score, cost or turns. Tools are options, not requirements: an
[Agno](https://docs.agno.com) agent ([agents/README.md](../agents/README.md#agno-agents)), skills, an
existing MCP server (`dct mcp serve`) or your own. Each agent's README lists a few to try. A skill or
a tool that does not move the numbers is context you pay for on every run.

**Key enabler: a shared semantic model.** A dark factory only works when every station means
the same thing by "revenue" or "customer". The data shows what happened; how Fernhill *counts* it
lives in people's heads, in your [interview notes](interviews.md). The baseline agents never see
those notes, and the final is mostly graded on them. Agents are good at finding traps that are
visible in the data; they cannot guess a finance rule. Writing Fernhill's metrics down once, as a
skill, as dbt semantic models, or as an [Apache Ossie](https://ossie.apache.org/) model served over
MCP, gives intake, implement, governance and bi one source of truth, and it carries over to the
hidden product. [ODCS](https://bitol-io.github.io/open-data-contract-standard/) is its sibling: Ossie
says what the numbers *mean*, an ODCS contract says what the product *guarantees*.

**Practice runs.** The practice run is the end-to-end benchmark: the same workflow and the same
scoring as the final, with a public product as the oracle. Run it in your fork (Actions →
*competition · final challenge*, with your fork, a commit SHA and `oracle: marketing_performance`)
or on your laptop ([competition.md](competition.md#trying-it-locally)). Station benchmarks are fast
and cheap, a practice run is slow and expensive: agree on a budget per team on Thursday.

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
  cases under `benchmark/cases/`. Python packages are fixed: if you need one, ask on Thursday and it
  is added for everyone.
- **Improve at least one agent**, with a measured gain on its station benchmark. How is up to you.
  A line of untouched baselines does not qualify for the podium.
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

- Before the kick-off: the baseline's station scores and its practice-run score, cost and duration
  are on the board. They depend on the model, so they are not in the repository.
- On Thursday, check that every team has one agent going round the loop: a score, a trace read, a
  change measured. A team stuck on tooling goes back to the baseline agent and changes its prompt.
- Pull requests from forks need a maintainer's approval before the repository's own checks
  (`ci.yml`) run on them.
- The default model is `google/gemma-4-31b-it` (OpenRouter), small, open and cheap on purpose: the baseline line
  should show how the factory works and still leave most of the points on the table. An `agent.yaml`
  can set any OpenRouter model (`model: qwen/qwen4-max`); that is a lever, and the cheapest one, so
  expect every team to try it. Do not set `FACTORY_MODEL` for the final: it overrides only
  `model: default`, but it would make the baseline line a moving target. Costs are what OpenRouter
  reports per run, the same way for every model.
