---
name: dbt-duckdb
description: Conventions and gotchas for writing dbt models on Fernhill's DuckDB warehouse - use when creating or fixing models, YAML contracts or tests in warehouse/.
---

# dbt on DuckDB at Fernhill

This is an *example skill* shipped disabled with the baseline implement agent. Enable it
in `agents/implement/agent.yaml` (`skills: [dbt-duckdb]`) and measure whether it helps.

## Project conventions
- Mart models live in `warehouse/models/marts/<product_id>/`, documented in `_<product_id>.yml`.
- Build on `fct_orders`, `fct_order_items`, `dim_customers`, `dim_products` and `stg_*`. Never `source()`.
- All amounts in marts are EUR (`*_eur`); the core facts are already converted.
- Every model in schema `main` (custom schema names are ignored by `generate_schema_name`).

## Contracts
Contracts are enforced, so `data_type` must match what DuckDB produces:
- `count(*)` -> `bigint`; `sum(<integer>)` -> `hugeint`; `sum(<double>)` -> `double`
- `date_trunc('month', <date>)` returns a `timestamp` - cast it: `cast(date_trunc('month', d) as date)`
- integer / integer -> `double` in DuckDB (no integer division surprises)

## Tests (dbt >= 1.10 syntax)
```yaml
data_tests:
  - unique_combination_of_columns:
      arguments:
        combination_of_columns: [month, category]
columns:
  - name: return_rate
    data_tests:
      - accepted_range:
          arguments: {min_value: 0, max_value: 1}
```

## DuckDB SQL reminders
- `datediff('month', a, b)`, `date_add(d, interval 3 month)`, `arg_min(value, ordering_col)`
- `range(0, n)` + `unnest` builds a spine
- `count(distinct ...)` is exact; `approx_count_distinct` is not
