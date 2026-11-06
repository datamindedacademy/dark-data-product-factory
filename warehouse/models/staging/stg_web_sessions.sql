select
    session_id,
    customer_id,
    started_at,
    cast(started_at as date) as session_date,
    traffic_source,
    device,
    pageviews,
    converted_order_id,
    converted_order_id is not null as is_converted
from {{ source('raw', 'web_sessions') }}
