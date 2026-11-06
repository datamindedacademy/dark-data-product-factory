-- Deduplicate replayed ingestion loads: keep the latest load per order_id.
with ranked as (
    select
        *,
        row_number() over (partition by order_id order by _loaded_at desc) as _rn
    from {{ source('raw', 'orders') }}
)

select
    order_id,
    customer_id,
    ordered_at,
    cast(ordered_at as date) as order_date,
    channel,
    store_id,
    status,
    status = 'cancelled' as is_cancelled,
    currency,
    cast(shipping_fee as double) as shipping_fee_local,
    discount_code
from ranked
where _rn = 1
