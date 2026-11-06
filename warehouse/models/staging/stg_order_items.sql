select
    order_item_id,
    order_id,
    product_id,
    quantity,
    cast(unit_price as double) as unit_price_local,
    cast(discount_amount as double) as discount_local,
    cast(unit_price as double) * quantity - cast(discount_amount as double) as net_amount_local
from {{ source('raw', 'order_items') }}
