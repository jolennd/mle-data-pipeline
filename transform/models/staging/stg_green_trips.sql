{{ config(materialized='table') }}

-- Typed and renamed trips. ehail_fee is dropped (always null in January).
-- Rows with no pickup time, or a pickup date outside the range, are left out here;
-- the loader report counts them (ADR 2). A missing total_amount is kept and flagged.
select
    VendorID                                 as vendor_id,
    lpep_pickup_datetime                     as pickup_datetime,
    lpep_dropoff_datetime                    as dropoff_datetime,
    cast(lpep_pickup_datetime as date)       as pickup_date,
    store_and_fwd_flag,
    RatecodeID                               as ratecode_id,
    PULocationID                             as pickup_location_id,
    DOLocationID                             as dropoff_location_id,
    passenger_count,
    trip_distance,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    cast(total_amount as decimal(12, 2))     as total_amount,
    total_amount is null                     as is_total_amount_missing,
    payment_type,
    trip_type,
    congestion_surcharge,
    cbd_congestion_fee,
    loaded_at,
    source_partition
from {{ source('raw', 'raw_green_trips') }}
where lpep_pickup_datetime >= cast('{{ var("range_start") }}' as timestamp)
  and lpep_pickup_datetime <  cast('{{ var("range_end") }}' as timestamp)
