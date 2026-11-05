-- A2: staged total_amount total equals mart revenue total, within 0.01. Returns a row when they differ.
select s.total as staged_total, m.total as mart_total
from (select coalesce(sum(total_amount), 0) as total from {{ ref('stg_green_trips') }}) s,
     (select coalesce(sum(revenue), 0) as total from {{ ref('mart_daily_revenue') }}) m
where abs(s.total - m.total) > 0.01
