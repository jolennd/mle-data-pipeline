-- Accepted range: every mart day has at least one trip. Returns violations.
select * from {{ ref('mart_daily_revenue') }} where trip_count < 1
