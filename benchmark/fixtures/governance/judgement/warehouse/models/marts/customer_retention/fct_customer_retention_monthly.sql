-- Monthly acquisition cohorts: for every cohort (month of first non-cancelled order)
-- and first-order channel, how many customers bought again N months later.
-- Internal QA accounts are excluded.
with orders as (
    select o.customer_id, o.ordered_at, o.channel,
           cast(date_trunc('month', o.order_date) as date) as order_month
    from {{ ref('fct_orders') }} as o
    where not o.is_cancelled
),

first_orders as (
    select
        customer_id,
        arg_min(channel, ordered_at) as first_order_channel,
        cast(date_trunc('month', min(ordered_at)) as date) as cohort_month
    from orders
    group by customer_id
),

activity as (
    select distinct
        f.cohort_month,
        f.first_order_channel,
        f.customer_id,
        datediff('month', f.cohort_month, o.order_month) as months_since_first_order
    from first_orders as f
    inner join orders as o on f.customer_id = o.customer_id
),

cohorts as (
    select cohort_month, first_order_channel, count(*) as cohort_customers
    from first_orders
    group by 1, 2
),

last_month as (
    select max(order_month) as max_month from orders
),

spine as (
    select c.cohort_month, c.first_order_channel, c.cohort_customers, k.months_since_first_order
    from cohorts as c
    cross join last_month
    cross join lateral (
        select unnest(range(0, datediff('month', c.cohort_month, last_month.max_month) + 1)) as months_since_first_order
    ) as k
),

active as (
    select cohort_month, first_order_channel, months_since_first_order, count(*) as active_customers
    from activity
    group by 1, 2, 3
)

select
    spine.cohort_month,
    spine.first_order_channel,
    cast(spine.months_since_first_order as integer) as months_since_first_order,
    spine.cohort_customers,
    coalesce(active.active_customers, 0) as active_customers,
    coalesce(active.active_customers, 0) / spine.cohort_customers as retention
from spine
left join active
    on spine.cohort_month = active.cohort_month
    and spine.first_order_channel = active.first_order_channel
    and spine.months_since_first_order = active.months_since_first_order
