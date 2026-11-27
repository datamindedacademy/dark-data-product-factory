# Dark data factory

Capstone project for the AI engineering bootcamp. From Thursday afternoon to Friday your team builds
up a **dark factory**: a line of AI agents that answers a business request from the company's data,
with nobody in the loop. On Friday every team's factory answers a request nobody has seen, and an
automated benchmark picks the winner ([docs/capstone-day.md](docs/capstone-day.md)).

```
 request ──▶ intake ──▶ spec.json ──▶ implement ──▶ answers.json ──▶ review ──▶ answers
 (issue.md)    │                          ▲                             │
               ▼                          └──────── rework ◀────────────┘
        can't be answered:
        questions back to the requester
```

The company is **Fernhill Outfitters**, a fictional outdoor-gear retailer: a web shop, an app and
six stores in Belgium, the Netherlands, France and the UK. Its data is two years of orders, returns,
customers and web sessions, as CSV files in `data/raw/`. Realistic, so messy.

A request is a list of numbered questions. The answers go in `answers.json`, one number or one
small table per question, in the format the request shows. That's what gets graded.

Each station has a working, deliberately plain **baseline agent** (`agents/<station>/agent.py`, an
[Agno](https://docs.agno.com) agent) and a **benchmark** (`benchmark/cases/<station>/`) that scores
it. You make the agents better by giving them context: instructions, skills, tools, MCP servers.
Intake, implement and review are the line; any other agent you add is your choice
([agents/README.md](agents/README.md)).

## Quick start

In a GitHub Codespace the devcontainer installs everything and starts Phoenix; it asks for an
OpenRouter key (`LLM_API_KEY`). On a laptop:

```bash
uv sync --extra dev                  # Python 3.15 (see .python-version)
source .venv/bin/activate
pytest -q                            # checks the factory and the benchmark, no LLM calls

export LLM_API_KEY=...               # an OpenRouter key, as in the other courses
make phoenix                         # in a second terminal: every agent run is a trace at http://localhost:6006
factory bench run intake --repeat 3  # the baseline score of a station
factory bench report                 # everything you ran, best first
factory line --issue benchmark/products/category_performance/issue.md   # the whole line
factory score runs/<the line run>    # its score, the way the final scores it
```

Without an API key you can still look around: `factory bench run <station> --oracle` grades the
right answers (always 1.0) and shows what the graders check.

On GitHub, label an issue `data-request` and `.github/workflows/factory-build.yml` runs the line and
posts the answers on the issue. The final runs in `.github/workflows/competition.yml`
([docs/competition.md](docs/competition.md)).

## Repository map

```
data/raw/             Fernhill's data: one CSV per table
agents/<station>/     The line: agent.py, instructions.md, README.md          ← yours
agents/line.yaml      Which stations run, how many rework rounds              ← yours
benchmark/
  cases/<station>/    Benchmark cases (YAML) and the files they need          ← yours
  products/           Practice requests with their right answers
  stages/             Setup and graders per station
factory/              The base agent, the line, the runner and tracing, scoring, the CLI
docs/                 The capstone, the interviews, the benchmark, the final
slides/               Kick-off slides (Slidev, Dataminded theme)
```

## Documentation

- [docs/capstone-day.md](docs/capstone-day.md): the two days, what the final scores, the rules (start here)
- [docs/interviews.md](docs/interviews.md): who is who at Fernhill, and the headlines of the interview recording
- [agents/README.md](agents/README.md): how to improve an agent
- [docs/benchmark.md](docs/benchmark.md): how grading works, how to write your own cases
- [docs/competition.md](docs/competition.md): the final, for facilitators
