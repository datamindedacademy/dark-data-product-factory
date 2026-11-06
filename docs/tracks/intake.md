# Track: Intake agent

**Station.** A stakeholder files a GitHub issue. The intake agent investigates the
warehouse and writes an *executable* spec (`output/spec.yaml`): purpose, business
questions, metric definitions, output models, data quality notes and acceptance checks
that will later prove the implementation right or wrong. When the request cannot be
built as asked, it says so (`needs_clarification` / `infeasible`) instead of inventing.

**Why it matters.** Every later station inherits the intake's mistakes. A missed trap
(QA accounts, cancelled orders, GBP) becomes a wrong number on a dashboard.

```bash
factory run intake --case intake-01-category
factory bench run intake --repeat 3
factory run intake --issue path/to/new_issue.md      # any issue
```

**Seed cases.** Three clear requests (category revenue, marketing ROAS, retention
cohorts), one that asks for data that does not exist (footfall, m²), one that is
infeasible (NPS without survey data).

**Ideas to improve**
- A skill on "how Fernhill's data works": the business rules and the known traps. Where
  does that knowledge come from without copying golden specs? Investigate the data and
  write it down - that is the job of a data team.
- A skill on writing acceptance checks: prefer `matches_reference` against staging,
  check grain, check the trap (e.g. "no QA customers in the output").
- Better data tools: enable `list_tables` / `describe_table`, or write a `profile_column`
  or `search_catalog` tool on top of `warehouse/target/manifest.json` (descriptions!).
- Make it validate its own acceptance checks: run each `reference_sql` before finishing.
- A clarification policy: what is a blocker vs. an assumption?
- Stretch: read the issue from GitHub (`gh issue view`) and post the open questions back.

**Benchmark ideas.** An issue with a hidden currency trap; an issue that mixes two
products; an issue whose requester uses a different word for a metric than the warehouse
(semantic layer!); judge calibration for spec quality.
