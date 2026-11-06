# Fernhill data product standards

Every data product merged into `warehouse/` must satisfy these rules. Each rule has
a stable ID: reviewers, the governance agent and the benchmark refer to rules by ID.

A **data product** is a set of mart models under `warehouse/models/marts/<product_id>/`
that share `meta.data_product: <product_id>`, plus one dashboard board in
`warehouse/charts/<product_id>.yml`.

| ID | Rule | Checked by `factory checkup`? |
|----|------|------|
| GOV-001 | Mart model names start with `fct_` (events/facts, one row per event or per period) or `dim_` (entities). | yes |
| GOV-002 | Every mart model has a description of at least 30 characters that states its grain. | partly (length only) |
| GOV-003 | Every column of a mart model has a non-empty description. | yes |
| GOV-004 | Every mart model declares its grain in `meta.grain` (list of columns) **and** has a data test enforcing it: `unique` on the single grain column, or `unique_combination_of_columns` on the grain list. | yes |
| GOV-005 | Every mart model has `meta.owner` (a team) and `meta.data_product` (the product id). | yes |
| GOV-006 | Columns that hold personal data (names, e-mail, phone, street address, IP address, free text written by a customer) are tagged `meta: {pii: true}`. Data products other than `core` must **not** expose PII columns at all. | no – needs judgement |
| GOV-007 | Mart models enforce a contract: `config.contract.enforced: true` and a `data_type` on every column. | yes |
| GOV-008 | Monetary columns carry their currency as suffix (`_eur`). Ratios are suffixed `_rate` or `_pct`, are stored as fractions (0–1) and have an `accepted_range` test (0..1). | no – needs judgement |
| GOV-009 | Mart models never select from `source()` directly; they build on staging (`stg_`) or other marts. | yes |
| GOV-010 | Every data product has a dashboard board in `warehouse/charts/<product_id>.yml` that passes `dct validate`, and the board's queries read from the product's own mart models. | no – needs judgement |
| GOV-011 | Business rules are applied consistently with the rest of the warehouse: cancelled orders are excluded from revenue, internal QA accounts (e-mail domain `fernhill.test`) are excluded from every customer-facing metric, and amounts in GBP are converted to EUR with `stg_fx_rates`. | no – needs judgement |

## Reporting violations

Report one violation per rule per model (add the column for column-level rules).
For product-level rules (GOV-010) use the product id as the model name.

## Notes for implementers

* Put product models in `warehouse/models/marts/<product_id>/` with one YAML file
  `_<product_id>.yml` describing them.
* Reuse `fct_orders`, `fct_order_items`, `dim_customers` and `dim_products` instead of
  re-deriving from staging when you can.
* Generic tests available in this project: `unique`, `not_null`, `accepted_values`,
  `relationships`, `unique_combination_of_columns`, `accepted_range`.
  dbt ≥ 1.10 syntax: put test arguments under `arguments:`.
