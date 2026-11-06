select
    c.customer_id,
    c.first_name,
    c.email,
    cast(date_trunc('month', c.first_ordered_at) as date) as cohort_month,
    first_orders.channel as first_order_channel
from {{ ref('dim_customers') }} as c
inner join (
    select customer_id, arg_min(channel, ordered_at) as channel
    from {{ ref('fct_orders') }}
    where not is_cancelled
    group by customer_id
) as first_orders on c.customer_id = first_orders.customer_id
