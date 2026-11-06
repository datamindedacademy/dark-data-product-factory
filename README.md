# Dark data product factory

Capstone project for the AI engineering bootcamp. You will build one station of a
**dark factory for data products**: a line of AI agents that turns a stakeholder's
request into a tested dbt data product with a dashboard, with no human in the loop.

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
The baselines are deliberately plain. Your job: pick a station, measure the baseline,
then improve the agent through its context (system prompt, skills, tools, MCP servers,
model and effort) and show the improvement with numbers.

## Quick start

```bash
uv sync --extra dev          # Python 3.15 (see .python-version), installs dbt-duckdb, dbt charts, checkup, the Agent SDK
source .venv/bin/activate
factory setup                # generates the warehouse and builds the dbt project (~10 s)
pytest -q                    # checks the benchmark itself, no LLM calls (~5 min)

export ANTHROPIC_API_KEY=...         # or log in with `claude` - the Agent SDK uses the same auth
factory bench list
factory run intake --case intake-01-category        # one run, prints the grades
factory bench run intake --repeat 3                 # the baseline score for your station
factory bench report                                # leaderboard of everything you ran
factory e2e --issue benchmark/products/category_performance/issue.md   # the whole line
```

In production the factory runs as a **CI pipeline** on GitHub Actions: label an issue
`data-product-request` and the line builds a branch, opens a PR, reviews, governs, reworks
and (optionally) merges it. See [docs/ci.md](docs/ci.md); every CI step is a `factory ci`
command you can run locally.

Without an API key you can still explore everything: `factory bench run <station> --oracle`
grades the golden answers (should be 1.0) and shows you exactly what the graders check.

## The stations (pick one per team)

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
agents/<station>/     Baseline agents: agent.yaml, system_prompt.md, prompt.md, skills/   ← you edit these
factory/              The factory: contracts, workspaces, agent runner + tracing, tools, e2e line, CI stations, CLI
.github/workflows/    The factory as CI: factory-build (issue → PR), factory-pr (gates, review, rework, merge), ...
benchmark/
  products/           Golden data products: issue, spec, models, dashboard (the answer keys)
  cases/<station>/    Benchmark cases (YAML)                                            ← you add these
  stages/             Setup, oracle and graders per station
  fixtures/           Planted-defect variants (review, governance) and the trace generator (line manager)
docs/                 Day plan for facilitators, architecture, benchmark guide, track briefs
tests/                Tests of the benchmark itself (oracle = 1.0, doing nothing = 0, defects are caught)
```

## Documentation

- [docs/capstone-day.md](docs/capstone-day.md) – the day: schedule, deliverables, scoring (facilitators start here)
- [docs/architecture.md](docs/architecture.md) – contracts between stations, workspaces, runner, traces
- [docs/ci.md](docs/ci.md) – the factory as a GitHub Actions pipeline (issue → PR → merge)
- [docs/benchmark.md](docs/benchmark.md) – how grading works and how to design your own cases and graders
- [agents/README.md](agents/README.md) – anatomy of an agent and the levers you can pull
- [warehouse/README.md](warehouse/README.md) – Fernhill's data
