# Capstone

**The goal.** By Friday 14:00 your team owns a dark factory: a line of agents that turns a request
into correct answers, with nobody in the loop. Then the organisers open a request nobody has seen,
every team's factory answers it in the same CI pipeline, and an automated benchmark picks the winner.

You don't start from zero. Each station of the line (intake, implement, review) has a working,
deliberately plain baseline agent, and the repository has a benchmark with cases for each. Teams of
2 to 4. Each team forks the repository and owns `agents/` and `benchmark/cases/` in its fork.

**How you work: one agent, the whole loop, then the next.**

1. **Benchmark.** Write a few cases for the agent and score it as it is.
2. **Traces.** Read the traces of the cases that lost points: what went wrong?
3. **Context.** Change one thing: the instructions, a skill, a tool, an MCP server.
4. **Repeat.** Run the benchmark again. Better: keep the change. Worse: undo it.

On **Thursday afternoon** the whole team takes one agent through that loop. On **Friday** you take
the same loop to as many other agents as you want, or add a station of your own. Which agent comes
next is a judgement call. [agents/README.md](../agents/README.md) has the commands.

## What the final scores

1. **Are the answers right?** (70 points) Each question of the request has one right answer, a
   number or a small table. Within 0.5% counts as right. Does your factory know Fernhill's rules
   (which orders count, test accounts, currencies, returns) and avoid the classic mistakes (counting
   an order twice, the wrong period, a table nobody maintains any more)? Does it check its own work?
2. **Does it finish on its own?** Nobody answers questions during the final. When a request is
   ambiguous but answerable, does your factory make an assumption and answer, or does it stop?
3. **What did it cost?** (15 points) Dollars and minutes for the whole line, counted only as far as
   the answers are right.
4. **Is your own benchmark sound?** (15 points) Three new cases that score 0 when the agent does
   nothing and 1 for the right answer.
5. **Does it generalise?** The final asks about things the practice requests hardly touch. Did you
   teach your factory how Fernhill's data works, or what three known requests look like?

The exact formula is in [competition.md](competition.md#scoring-100-points).

## Schedule

Clock times follow from the bootcamp schedule. TODO: fill them in.

| When | Block | You do |
|---|---|---|
| Thursday afternoon | **Kick-off** | Fork, open a Codespace (or `uv sync --extra dev`). Demo of the line on one request. The rules and the questions above. Hand-out: the interview recording, what Fernhill's people told you and what no agent knows yet ([interviews.md](interviews.md) has who is who). |
| Thursday afternoon | **One agent, the whole loop** | Pick the agent with the most points to win. Benchmark it, read its traces, change its context, repeat. Add cases of your own as you find failures. |
| Friday | **More agents** | The same loop on other agents, or a new station. Check now and then that the whole line gets better: `factory line` on a practice request, then `factory score`. |
| Friday | **Freeze** | Open a pull request from your fork to the organisers' repository. Title: your team name in capitals. Its head commit is what runs. |
| Friday | **Final** (45') | The organisers open the request and start the pipeline for every team. You watch, and prepare a three-minute story. |
| Friday, before 14:00 | **Results and retro** | Leaderboard. Per team: the change that mattered most, one thing that did not work, and how well your benchmark predicted your final score. |

### Notes

**Benchmark.** `factory bench run implement --agent agents/<x> --label v1 --repeat 3`, then
`factory bench report`. Your cases and every file they need live under `benchmark/cases/`; see
[benchmark.md](benchmark.md).

**Traces.** Every run writes `trace.jsonl` and `summary.json` under `runs/`. With Phoenix running
(`make phoenix`, or automatically in a Codespace) every run is also a trace at http://localhost:6006,
with the model calls, the tool calls, and the reasoning when an agent reasons (`effort=`).

**Context.** Anything that moves the score, the cost or the turns. Tools are options, not
requirements. Each agent's README lists a few to try. A skill or a tool that doesn't move the
numbers is context you pay for on every run.

**One set of definitions.** A dark factory only works when every station means the same thing by
"revenue" or "customer". The data shows what happened; how Fernhill *counts* it lives in people's
heads, in the [interviews](interviews.md). Writing those rules down once, as a skill or as a
semantic model, gives intake, implement and review one source of truth, and it carries over to the
final.

**Practice runs.** `factory line` on a practice request is the final in small: the same line and the
same scoring, with public right answers. It is slower and costs more than a station benchmark: agree
on a budget per team on Thursday.

## The final

- The request is a GitHub issue in the organisers' repository: numbered questions, and an *Answers*
  section with the JSON format to answer in.
- Your factory runs in the organisers' pipeline (`.github/workflows/competition.yml`), at the commit of
  your pull request at the freeze. From your fork it takes `agents/` and `benchmark/cases/`.
  Everything else is the organisers' code: the base agent, the line, the data, the graders, the
  dependencies.
- The line is `factory line`: the stations in your `agents/line.yaml`, with as many rework rounds as
  it allows. If intake does not return a `ready` spec, the line stops and there are no answers.
- One run, 45 minutes, on an API key with a spend limit. No reruns for bad luck.
- The score is posted on your pull request.

## Rules

- **Your factory, the organisers' pipeline.** You may change anything under `agents/` and add cases
  under `benchmark/cases/`. Python packages are fixed: if you need one, ask on Thursday and it is
  added for everyone.
- **Improve at least one agent**, with a measured gain on its benchmark. A line of untouched
  baselines does not qualify for the podium.
- **No right answers in the agents' context.** No copies of `benchmark/products/*/answers.json` or
  numbers from them in instructions, skills or tools. Knowledge about
  Fernhill's data is fine, and is exactly what a good skill holds.
- **No human in the loop.** The agents may not fetch anything somebody wrote after the request was
  opened. Facilitators read the diff of the winning teams.
- **Measure before you claim.** One run proves nothing. Agents are noisy: repeat, and look at the spread.

## For facilitators

Preparation, secrets, the hidden right answers, the freeze-and-reveal commands and the loopholes
are in [competition.md](competition.md). On the day:

- Before the kick-off: the baseline's station scores and its practice-run score, cost and duration
  are on the board. They depend on the model, so they are not in the repository.
- On Thursday, check that every team has one agent going round the loop: a score, a trace read, a
  change measured. A team stuck on tooling goes back to the baseline agent and changes its instructions.
- The default model is `google/gemma-4-31b-it` (OpenRouter): small, open and cheap on purpose, so the
  baseline shows how the factory works and leaves most of the points on the table. An agent can use
  any OpenRouter model (`model="qwen/qwen4-max"`). That is a lever, and the easiest one, so expect
  every team to try it.
