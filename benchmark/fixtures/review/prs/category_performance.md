# Add data product `category_performance`

Closes #101.

Adds `fct_category_revenue_monthly` (month x category) with sales, refunds, net
revenue and return rate in EUR, plus the `category_performance` dashboard.

- excludes cancelled orders and internal QA accounts
- refunds attributed to the order month, converted at the order's FX rate
- tests: grain, not_null, return_rate in [0, 1]

`dbt build` passes locally.
