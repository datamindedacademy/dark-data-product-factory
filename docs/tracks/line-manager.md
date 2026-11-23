# Track: Factory line manager (choose your own adventure)

**Station.** Watches the factory instead of building products. Reads `summary.json` and
`trace.jsonl` of many runs, finds recurring failures, bottlenecks and waste, and
recommends concrete changes to the other agents (`output/recommendations.json` +
`output/report.md`).

```bash
python benchmark/fixtures/line_manager/generate_runs.py runs/synthetic-week   # look at the data
factory run line_manager --case line_manager-01-week
factory bench run line_manager --repeat 3
```

**Seed case.** A synthetic week of ~120 runs with five planted recurring problems
(see the generator's docstring - don't read it before you have tried!). Real traces from
the other teams' benchmark runs have the same format: use them in the afternoon.

**Ideas to improve**
- Don't make the model read 120 traces. Give it analytics: DuckDB reads JSONL
  (`select * from read_json_auto('input/runs/*/trace.jsonl')`) - a
  `query_traces` tool, or a skill with ready-made queries (errors per tool, turns per
  agent, cost share, retries of the same command).
- Quantify: every recommendation with evidence (runs, counts, $) and expected impact.
- Close the loop: let it write the change (a patch to `agents/`), then re-run the benchmark
  of that station to verify. That is a self-improving factory.
- Stretch: a live dashboard of the factory itself as a dbt charts board.

**Benchmark ideas.** Generate a week with a different seed and a new pattern; a week
with a red herring (one very expensive run that is not recurring).
