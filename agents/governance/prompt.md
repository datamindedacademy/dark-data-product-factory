Check the data product `$product_id` (models in `warehouse/models/marts/$product_id/`,
dashboard in `warehouse/charts/$product_id.yml`) against every rule in
`standards/data-product-standards.md`.

Write the result to `output/governance.json`:

```json
{
  "product_id": "$product_id",
  "compliant": true | false,
  "checked_rules": ["GOV-001", ...],
  "violations": [
    {"rule_id": "GOV-006", "model": "fct_x", "column": "email", "message": "..."}
  ]
}
```

Report one violation per rule per model (add `column` when the rule is about a column).
Validate the file with `factory validate governance output/governance.json`.
