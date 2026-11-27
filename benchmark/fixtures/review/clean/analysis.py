"""Category performance: net revenue and returns per category (request 101)."""
import json
from pathlib import Path

import duckdb

con = duckdb.connect()
for f in Path("data").glob("*.csv"):
    con.execute(f"create view {f.stem} as select * from read_csv_auto('{f}')")

con.execute("""
create table lines as
with latest as (   -- ingestion replays orders: keep the latest load
  select * from orders qualify row_number() over (partition by order_id order by _loaded_at desc) = 1
),
counted as (       -- revenue = shipped or delivered, no test accounts
  select o.order_id, cast(o.ordered_at as date) as d, coalesce(fx.rate_to_eur, 1.0) as fx
  from latest o
  left join fx_rates fx on fx.currency = o.currency and fx.rate_date = cast(o.ordered_at as date)
  where o.status in ('shipped', 'delivered')
    and o.customer_id not in (select customer_id from customers where email like '%@fernhill.test')
),
refunds as (       -- refunds for damaged goods are claimed back from the carrier
  select order_item_id, sum(quantity) as qty, sum(refund_amount) filter (where reason <> 'damaged') as lost
  from returns group by 1
)
select c.d,
       case lower(trim(p.category)) when 'camping kitchen' then 'Camping Kitchen' when 'sleeping bags' then 'Sleeping Bags'
            else upper(substr(trim(p.category), 1, 1)) || lower(substr(trim(p.category), 2)) end as category,
       i.quantity as units, coalesce(r.qty, 0) as returned,
       (i.unit_price * i.quantity - i.discount_amount - coalesce(r.lost, 0)) * c.fx as net_revenue
from order_items i
join counted c using (order_id)
join products p using (product_id)
left join refunds r using (order_item_id)
where c.d between '2025-01-01' and '2025-12-31'
""")


def rows(sql):
    return {str(k): v for k, v in con.execute(sql).fetchall()}


answers = {
    "Q1": rows("select category, round(sum(net_revenue)) from lines group by 1"),
    "Q2": rows("select category, round(sum(returned) / sum(units), 4) from lines group by 1"),
    "Q3": rows("select strftime(d, '%Y-%m'), round(sum(net_revenue)) from lines where category = 'Footwear' group by 1"),
}
Path("output/answers.json").write_text(json.dumps(answers, indent=2))
