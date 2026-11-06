-- Monthly sales, refunds and returns per product category.
-- Excludes cancelled orders and internal QA accounts; refunds are attributed
-- to the month of the original order and converted at the order's FX rate.
with customers as (
    select customer_id
    from {{ ref('dim_customers') }}
    where email not like '%@fernhill.test'
),

items as (
    select
        i.order_item_id,
        i.order_id,
        cast(date_trunc('month', i.order_date) as date) as month,
        p.category,
        i.quantity,
        i.net_amount_eur,
        o.fx_rate_to_eur
    from {{ ref('fct_order_items') }} as i
    inner join {{ ref('fct_orders') }} as o on i.order_id = o.order_id
    inner join {{ ref('dim_products') }} as p on i.product_id = p.product_id
    inner join customers as c on i.customer_id = c.customer_id
    where not i.is_cancelled
),

returns as (
    select
        order_item_id,
        sum(returned_quantity) as returned_quantity,
        sum(refund_local) as refund_local
    from {{ ref('stg_returns') }}
    group by order_item_id
)

select
    items.month,
    items.category,
    count(distinct items.order_id) as orders,
    sum(items.quantity) as units_sold,
    coalesce(sum(returns.returned_quantity), 0) as units_returned,
    round(sum(items.net_amount_eur), 2) as sales_eur,
    round(coalesce(sum(returns.refund_local * items.fx_rate_to_eur), 0), 2) as refunds_eur,
    round(sum(items.net_amount_eur) - coalesce(sum(returns.refund_local * items.fx_rate_to_eur), 0), 2) as net_revenue_eur,
    coalesce(sum(returns.returned_quantity), 0) / sum(items.quantity) as return_rate
from items
left join returns on items.order_item_id = returns.order_item_id
group by items.month, items.category
