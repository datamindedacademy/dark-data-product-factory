# Track: BI agent

**Station.** Translates the purpose and questions of a data product into a dbt charts
board (`warehouse/charts/<id>.yml`) on top of the product's mart models. Every question
must be answered by a chart; query `notes` say which (`"Answers Q1 - ..."`).

```bash
factory run bi --case bi-01-category
factory bench run bi --repeat 3 --judge     # the judge reads the rendered board + data
cd runs/<run>/workspace/warehouse && dct serve   # look at it
```

**Graded on** `dct validate`, `dct render`, question coverage, lineage (reads the product's
models) and, with `--judge`, whether the rendered board answers each question.

**Ideas to improve**
- dbt charts ships agent skills: `dct skills chart` (and `dct init skills`) - install the
  relevant ones as skills of the agent and measure.
- Plug in dbt charts' own MCP server (`mcp: {dct: true}` in agent.yaml).
- A visualisation skill: chart type per question type, ratio-of-sums, KPIs for headline
  numbers, labels for business users.
- Visual verification: render to PNG and let the agent look at its own dashboard.
- Stretch: a semantic layer - metric definitions from the spec as reusable queries.

**Benchmark ideas.** A spec with a question that needs a table, not a chart; a product
with a ratio that must not be averaged; a judge-calibration case.
