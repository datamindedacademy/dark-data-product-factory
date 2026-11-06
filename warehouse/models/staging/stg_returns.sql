select
    return_id,
    order_item_id,
    returned_at,
    cast(returned_at as date) as return_date,
    quantity as returned_quantity,
    reason as return_reason,
    cast(refund_amount as double) as refund_local
from {{ source('raw', 'returns') }}
