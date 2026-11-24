# Dark data product factory

Capstone project for the AI engineering bootcamp. In one day your team builds up a
**dark factory for data products**: a line of AI agents that turns a stakeholder's
request into a tested dbt data product with a dashboard, with no human in the loop.
At the end of the day every team's factory builds a request nobody has seen, in CI, and
an automated benchmark picks the winner ([docs/capstone-day.md](docs/capstone-day.md)).

```
 GitHub issue ──▶ intake ──▶ spec.yaml ──▶ implement ──▶ dbt models ──▶ review ──▶ governance ──▶ bi ──▶ dbt charts board
                    │          (executable)      │                       │            │
                    ▼                            └──── rework loop ◀─────┴────────────┘
             needs clarification /
             infeasible → back to requester          line manager watches every run's trace and tunes the line
```

The company is **Fernhill Outfitters**, a fictional outdoor-gear retailer (web shop, app,
six stores in BE/NL/FR/UK). Its warehouse is a dbt project on DuckDB with two years of
synthetic but realistic, messy data (`warehouse/`). Dashboards are built with
[dbt charts](https://docs.getdbt.com/guides/dbt-charts) (`dct`).

Every station has a working **baseline agent** built with the Claude Agent SDK
(`agents/<station>/`) and a **benchmark** (`benchmark/cases/<station>/`) that scores it.
The baselines are deliberately plain. Your job: build your own agent for a station with
[Agno](https://docs.agno.com) (`agents/intake-agno/` is the starter), give it skills and
an MCP server, write benchmark cases, and use them to improve the whole line - with
numbers to show for it.

## Quick start

```bash
uv sync --extra dev          # Python 3.15 (see .python-version), installs dbt-duckdb, dbt charts, checkup, the Agent SDK, Agno
source .venv/bin/activate
factory setup                # generates the warehouse and builds the dbt project (~10 s)
pytest -q                    # checks the benchmark itself, no LLM calls (~4 min)

export ANTHROPIC_API_KEY=...         # the baselines also work with a `claude` login; Agno agents need the key
factory bench list
factory run intake --case intake-01-category        # one run, prints the grades
factory bench run intake --repeat 3                 # the baseline score for your station
factory bench report                                # leaderboard of everything you ran
factory run intake --agent-dir agents/intake-agno --case intake-01-category   # the Agno starter
factory e2e --issue benchmark/products/category_performance/issue.md   # the whole line
```

In production the factory runs as a **CI pipeline** on GitHub Actions: label an issue
`data-product-request` and the line builds a branch, opens a PR, reviews, governs, reworks
and (optionally) merges it. See [docs/ci.md](docs/ci.md); every CI step is a `factory ci`
command you can run locally. The final challenge runs in its own pipeline,
`competition.yml`, which builds and scores one team's line ([docs/competition.md](docs/competition.md)).

Without an API key you can still explore everything: `factory bench run <station> --oracle`
grades the golden answers (should be 1.0) and shows you exactly what the graders check.

## The stations (split your team across them, rebuild at least one with Agno)

Each person or pair owns one station; the rest of the line runs on its baseline. With four people,
take intake, implement, governance and bi: together they decide 80 of the 100 final points.

| Track | Input → output | What makes it hard | Brief |
|---|---|---|---|
| **Intake** | GitHub issue → executable spec (questions, metrics, acceptance SQL) | finding the data traps; knowing when to ask instead of invent | [docs/tracks/intake.md](docs/tracks/intake.md) |
| **Implement** | spec → dbt models that pass the acceptance checks (some hidden) | DuckDB + dbt contracts, business rules, standards | [docs/tracks/implement.md](docs/tracks/implement.md) |
| **Review** | PR on branch `feature` → approve / request changes + findings | catching subtle numeric bugs without crying wolf; docs drift | [docs/tracks/review.md](docs/tracks/review.md) |
| **Governance** | data product → standards violations (`GOV-0xx`) | the rules a linter cannot check: PII, naming, business rules | [docs/tracks/governance.md](docs/tracks/governance.md) |
| **BI** | spec + built models → dbt charts board | answering the questions, valid YAML, right chart types | [docs/tracks/bi.md](docs/tracks/bi.md) |
| **Line manager** (choose your own adventure) | traces of ~120 runs → recommendations | finding recurring waste in a lot of telemetry | [docs/tracks/line-manager.md](docs/tracks/line-manager.md) |

## Repository map

```
warehouse/            Fernhill's dbt + dbt charts project (DuckDB). The "company repo" agents work in.
standards/            Data product standards (rule ids GOV-001..011) used by review & governance.
agents/<station>/     The line: agent.yaml, system_prompt.md, prompt.md, skills/, agent.py (Agno)   ← yours
agents/intake-agno/   Starter Agno agent
factory/              The factory: contracts, workspaces, agent runner + tracing, tools, e2e line, CI stations,
                      final-challenge scoring, CLI
.github/workflows/    The factory as CI: factory-build (issue → PR), factory-pr (gates, review, rework, merge),
                      competition (the final challenge), ...
benchmark/
  products/           Golden data products: issue, spec, models, dashboard (the answer keys)
  cases/<station>/    Benchmark cases (YAML) and the files they need                    ← yours
  stages/             Setup, oracle and graders per station
  fixtures/           Planted-defect variants (review, governance) and the trace generator (line manager)
docs/                 Day plan, final challenge, architecture, CI, benchmark guide, track briefs
slides/               Kick-off slides that explain the capstone (Slidev, Dataminded theme)
tests/                Tests of the benchmark, the CI stations and the final scoring - no LLM calls
```

## Documentation

- [docs/capstone-day.md](docs/capstone-day.md) – the day: schedule, checkpoints, what the final is evaluated on, rules (start here)
- [docs/competition.md](docs/competition.md) – the final challenge for organisers: design, scoring, runbook, loopholes
- [docs/architecture.md](docs/architecture.md) – contracts between stations, workspaces, runner, traces
- [docs/ci.md](docs/ci.md) – the factory as a GitHub Actions pipeline (issue → PR → merge)
- [docs/benchmark.md](docs/benchmark.md) – how grading works and how to design your own cases and graders
- [agents/README.md](agents/README.md) – anatomy of an agent and the levers you can pull
- [warehouse/README.md](warehouse/README.md) – Fernhill's data
