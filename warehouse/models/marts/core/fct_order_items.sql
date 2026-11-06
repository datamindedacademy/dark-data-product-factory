-- One row per order line, amounts in EUR. Does not include returns (see stg_returns).
select
    items.order_item_id,
    items.order_id,
    orders.customer_id,
    items.product_id,
    orders.ordered_at,
    orders.order_date,
    orders.channel,
    orders.status,
    orders.is_cancelled,
    items.quantity,
    round(items.unit_price_local * orders.fx_rate_to_eur, 2) as unit_price_eur,
    round(items.discount_local * orders.fx_rate_to_eur, 2) as discount_eur,
    round(items.net_amount_local * orders.fx_rate_to_eur, 2) as net_amount_eur
from {{ ref('stg_order_items') }} as items
inner join {{ ref('fct_orders') }} as orders on items.order_id = orders.order_id
