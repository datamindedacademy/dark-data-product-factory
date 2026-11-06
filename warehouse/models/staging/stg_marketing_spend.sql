select spend_date, channel, cast(spend_eur as double) as spend_eur
from {{ source('raw', 'marketing_spend') }}
