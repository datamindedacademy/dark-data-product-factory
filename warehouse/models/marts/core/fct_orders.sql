-- One row per order. Monetary amounts converted to EUR at the daily rate of the order date.
with orders as (
    select * from {{ ref('stg_orders') }}
),

items as (
    select
        order_id,
        sum(quantity) as units,
        sum(unit_price_local * quantity) as gross_amount_local,
        sum(discount_local) as discount_local
    from {{ ref('stg_order_items') }}
    group by order_id
),

fx as (
    select * from {{ ref('stg_fx_rates') }}
)

select
    orders.order_id,
    orders.customer_id,
    orders.ordered_at,
    orders.order_date,
    orders.channel,
    orders.store_id,
    orders.status,
    orders.is_cancelled,
    orders.currency,
    coalesce(fx.rate_to_eur, 1.0) as fx_rate_to_eur,
    items.units,
    round(items.gross_amount_local * coalesce(fx.rate_to_eur, 1.0), 2) as gross_amount_eur,
    round(items.discount_local * coalesce(fx.rate_to_eur, 1.0), 2) as discount_eur,
    round((items.gross_amount_local - items.discount_local) * coalesce(fx.rate_to_eur, 1.0), 2) as net_amount_eur,
    round(orders.shipping_fee_local * coalesce(fx.rate_to_eur, 1.0), 2) as shipping_fee_eur
from orders
inner join items on orders.order_id = items.order_id
left join fx
    on fx.currency = orders.currency
    and fx.rate_date = orders.order_date
