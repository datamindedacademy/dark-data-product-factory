# Track: Governance agent

**Station.** Checks a data product against `standards/data-product-standards.md` and
reports violations by rule id (`output/governance.json`). The agent's `checkup` tool
runs [checkup](https://pypi.org/project/checkup/) with `warehouse/checkup.yaml`: the
checkup-dbt metrics plus a Fernhill plugin (`factory/checkup_plugin.py`) with one metric
per mechanical rule (GOV-001..005, 007, 009). The rest need judgement: PII (GOV-006),
naming of measures and ratios (GOV-008), dashboard (GOV-010), business rules (GOV-011).

```bash
cd warehouse && dbt parse && checkup run --tag data_product=marketing_performance
```

```bash
factory run governance --case governance-03-judgement
factory bench run governance --repeat 3
```

**Seed cases.** A compliant product (no false violations!), one with mechanical
violations, one that is green in checkup but breaks the judgement rules.

**Ideas to improve**
- Treat `checkup` as the first step, not the answer; give a method per judgement rule.
- Tools for the judgement rules: column profiling to detect PII by content, a check that
  the board exists and validates, SQL to test whether QA accounts are in the output.
- Write new checkup metrics for rules that *can* be made mechanical (e.g. the
  `accepted_range` part of GOV-008, the board-exists part of GOV-010, a PII-name heuristic
  for GOV-006): subclass `FernhillRuleMetric` / `DbtMetric` in `factory/checkup_plugin.py`,
  register the entry point in `pyproject.toml`, add it to `warehouse/checkup.yaml`.
  Measure what the LLM still adds on top.
- Use checkup's materializers: `--materializer html` for a report, `sqlalchemy` to keep
  history of product health over time.
- Precision matters: one violation per rule per model, exact model names.
- Stretch: suggest the fix as a patch, or wire it as a CI gate.

**Benchmark ideas.** PII hidden in a free-text column; a monetary column without `_eur`;
a board that reads raw tables; a product that is compliant but looks suspicious.
