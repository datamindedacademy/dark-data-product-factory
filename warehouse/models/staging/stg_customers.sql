select
    customer_id,
    first_name,
    last_name,
    lower(email) as email,
    country_code,
    signed_up_at,
    marketing_opt_in
from {{ source('raw', 'customers') }}
