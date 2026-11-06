select rate_date, currency, cast(rate_to_eur as double) as rate_to_eur
from {{ source('raw', 'fx_rates') }}
