Build the dashboard for the data product described in `input/spec.yaml`
(product id `$product_id`). Its mart models are already built in the warehouse.

Write the board to `warehouse/charts/$product_id.yml`. Every business question in the
spec must be answered by at least one chart. Give each query a `notes:` field saying
which questions it answers, e.g. `notes: "Answers Q1, Q3 - ..."`.

Make sure `dct validate` passes and `dct render` shows no errors.
