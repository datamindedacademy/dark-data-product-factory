select
    product_id,
    sku,
    product_name,
    category,
    subcategory,
    list_price_eur,
    unit_cost_eur,
    launched_at,
    is_active
from {{ ref('stg_products') }}
