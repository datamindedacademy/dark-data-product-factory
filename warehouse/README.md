# Fernhill Outfitters warehouse

dbt project on DuckDB (`warehouse.duckdb`, loaded by `factory setup` from
`data/raw/*.parquet`; 2024-01-01 .. 2025-12-31).

| Layer | Schema | Models |
|---|---|---|
| raw | `raw` | orders, order_items, products, customers, stores, returns, fx_rates, web_sessions, marketing_spend |
| staging | `main` | `stg_*` - renamed, typed, deduplicated (`stg_orders`), normalised categories (`stg_products`) |
| core marts | `main` | `fct_orders`, `fct_order_items`, `dim_customers`, `dim_products` (data product `core`) |
| products | `main` | `models/marts/<product_id>/` - built by the factory |

Dashboards are dbt charts boards in `charts/` (`dct validate`, `dct render`, `dct serve`).
Queries can use `{{ ref('model') }}`.

```bash
cd warehouse
dbt build                 # profiles.yml in this directory points at warehouse.duckdb
dct validate              # all boards
dct render charts/sales_overview.yml --format text
dct serve                 # live preview in the browser
```


