# Implement

Builds the spec as dbt models, tests and docs. Reworks them when review or governance send them back.

**In** `input/spec.yaml` (+ `input/feedback.md`) **Out** `warehouse/models/marts/<id>/`

**Try**
- dbt model contracts (`contract: {enforced: true}`), with the `skills/dbt-duckdb` skill
- The metric definitions intake wrote (dbt semantic models)
- `factory accept` and `checkup` before handing over
