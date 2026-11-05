{{ config(materialized='table') }}

-- One row per trip (ADR 13). trip_id hashes source_partition and the source columns, so
-- it is stable across reloads (loaded_at is left out). A null key maps to -1 (Unknown).
select
    md5(cast(row(
        source_partition, vendor_id, pickup_datetime, dropoff_datetime, store_and_fwd_flag,
        ratecode_id, pickup_location_id, dropoff_location_id, passenger_count, trip_distance,
        fare_amount, extra, mta_tax, tip_amount, tolls_amount, improvement_surcharge,
        total_amount, payment_type, trip_type, congestion_surcharge, cbd_congestion_fee
    ) as varchar))                          as trip_id,
    pickup_date,
    coalesce(payment_type, -1)              as payment_type,
    coalesce(vendor_id, -1)                 as vendor_id,
    coalesce(ratecode_id, -1)               as ratecode_id,
    pickup_location_id,
    dropoff_location_id,
    fare_amount,
    tip_amount,
    total_amount,
    trip_distance,
    passenger_count,
    source_partition
from {{ ref('stg_green_trips') }}
