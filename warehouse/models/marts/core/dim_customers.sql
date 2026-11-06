with orders as (
    select
        customer_id,
        min(ordered_at) as first_ordered_at,
        max(ordered_at) as last_ordered_at,
        count(*) as lifetime_orders
    from {{ ref('fct_orders') }}
    where not is_cancelled
    group by customer_id
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country_code,
    c.signed_up_at,
    c.marketing_opt_in,
    o.first_ordered_at,
    o.last_ordered_at,
    coalesce(o.lifetime_orders, 0) as lifetime_orders
from {{ ref('stg_customers') }} as c
left join orders as o on c.customer_id = o.customer_id
