-- Accepted range: staging holds only pickup dates inside the range (ADR 2). Returns violations.
select *
from {{ ref('stg_green_trips') }}
where pickup_date < cast('{{ var("range_start") }}' as date)
   or pickup_date >= cast('{{ var("range_end") }}' as date)
