select store_id, store_name, city, country_code, opened_at
from {{ source('raw', 'stores') }}
