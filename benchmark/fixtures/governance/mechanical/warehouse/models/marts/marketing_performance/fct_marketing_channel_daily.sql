-- Daily traffic, conversion, attributed revenue and spend per traffic channel.
-- A session converts when it placed an order that was not cancelled.
-- Sessions of internal QA accounts are excluded.
with qa as (
    select customer_id from {{ ref('dim_customers') }} where email like '%@fernhill.test'
),

orders as (
    select order_id, net_amount_eur
    from {{ ref('fct_orders') }}
    where not is_cancelled
),

sessions as (
    select
        s.session_date,
        s.traffic_source as channel,
        s.session_id,
        o.order_id,
        o.net_amount_eur
    from {{ ref('stg_web_sessions') }} as s
    left join orders as o on s.converted_order_id = o.order_id
    where s.customer_id is null or s.customer_id not in (select customer_id from qa)
),

traffic as (
    select
        session_date as date,
        channel,
        count(*) as sessions,
        count(order_id) as orders,
        coalesce(sum(net_amount_eur), 0) as net_revenue_eur
    from sessions
    group by 1, 2
),

spend as (
    select spend_date as date, channel, sum(cast(spend_eur as double)) as spend_eur
    from {{ source('raw', 'marketing_spend') }}
    group by 1, 2
)

select
    traffic.date,
    traffic.channel,
    traffic.sessions,
    traffic.orders,
    traffic.orders / traffic.sessions as conversion_rate,
    round(traffic.net_revenue_eur, 2) as net_revenue_eur,
    round(coalesce(spend.spend_eur, 0), 2) as spend_eur,
    spend.spend_eur is not null as is_paid_channel
from traffic
left join spend on traffic.date = spend.date and traffic.channel = spend.channel
