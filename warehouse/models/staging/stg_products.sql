select
    product_id,
    sku,
    product_name,
    -- merchandisers type categories by hand: normalise casing + whitespace
    case lower(trim(category))
        when 'camping kitchen' then 'Camping Kitchen'
        when 'sleeping bags' then 'Sleeping Bags'
        else upper(substr(trim(category), 1, 1)) || lower(substr(trim(category), 2))
    end as category,
    subcategory,
    cast(list_price as double) as list_price_eur,
    cast(unit_cost as double) as unit_cost_eur,
    launched_at,
    is_active
from {{ source('raw', 'products') }}
