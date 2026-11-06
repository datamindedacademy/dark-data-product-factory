Implement the data product specified in `input/spec.yaml`.

- Put the models in `warehouse/models/marts/<spec id>/` together with a YAML file
  documenting them.
- Build and test them with dbt.
- Check your work against the spec's acceptance checks:
  `factory accept input/spec.yaml --db warehouse/warehouse.duckdb`

Finish with a short summary of what you built.

If `input/feedback.md` exists, this is a rework round: the reviewers' and governance
findings are in that file. Address every finding.
