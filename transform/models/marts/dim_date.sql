{{ config(materialized='table') }}

-- One row per day from range_start to the day before range_end (ADR 13, ADR 2).
-- day_of_week is ISO: 1 is Monday, 7 is Sunday.
select
    cast(d as date)                       as pickup_date,
    isodow(cast(d as date))               as day_of_week,
    isodow(cast(d as date)) >= 6          as is_weekend,
    month(cast(d as date))                as month
from generate_series(
    cast('{{ var("range_start") }}' as date),
    cast('{{ var("range_end") }}' as date) - interval 1 day,
    interval 1 day
) as t(d)
