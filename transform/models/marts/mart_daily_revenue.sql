{{ config(materialized='table') }}

-- One row per pickup date. Revenue is total_amount summed as is, negatives included (ADR 1).
-- Built from the fact table (ADR 13).
select
    pickup_date,
    coalesce(sum(total_amount), 0) as revenue,
    count(*)                       as trip_count
from {{ ref('fct_trips') }}
group by pickup_date
