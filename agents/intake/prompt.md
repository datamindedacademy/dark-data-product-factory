A new data product request came in. It is in `input/issue.md`.

Write a spec for it to `output/spec.yaml` with these top-level keys:

```yaml
spec_version: 1
id: snake_case_product_id          # also the folder name under warehouse/models/marts/
title: ...
status: ready | needs_clarification | infeasible
purpose: ...                       # why the product exists, for whom, which decision it supports
requested_by: ...
business_questions:                # the questions the product must answer
  - id: Q1
    question: ...
    metrics: [...]
    dimensions: [...]
    acceptance:                    # executable checks on the output models
      - id: Q1.something
        description: ...
        sql: select ... from {{ ref('fct_x') }} ...
        expect: {type: equals, value: 123, tolerance: 0.001}
        # expect types: equals(value) | between(min,max) | row_count(value) | non_empty | empty
        #               | matches_reference(reference_sql: SQL on staging/core tables)
metrics: [{name, definition, expression}]
inputs: [{name: existing model or raw table, columns: [...], notes}]
data_quality_notes: [{issue, handling}]
outputs:                           # mart models to build
  - name: fct_...
    description: ...
    grain: [col, ...]
    columns: [{name, data_type, description, tests: [...], pii: false}]
dashboard: {title, audience, charts: ["Line chart of ... (Q1)", ...]}
assumptions: [...]
open_questions: [...]              # required when status is needs_clarification
infeasible_reason: ...             # required when status is infeasible
```

When you are done, validate the file with `factory validate spec output/spec.yaml`.
