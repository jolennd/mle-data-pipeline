# ADR 13: A star schema sits between staging and the daily mart
Status: accepted, built
Context: The deliverable is revenue per day. The same trips can answer other questions (by payment type, vendor, rate code), and a fact table with dimensions keeps those keys clean and tested.
Decision: The chain is raw_green_trips, stg_green_trips, fct_trips plus dimensions, mart_daily_revenue, then data/processed/daily_revenue.parquet. The deliverable does not change.
- fct_trips: one row per trip. trip_id is a hash of source_partition and all source columns. It is tested unique. If a month has exact duplicate rows, stop and report; do not deduplicate. Keys: pickup_date, payment_type, vendor_id, ratecode_id, pickup_location_id, dropoff_location_id. Measures: fare_amount, tip_amount, total_amount, trip_distance, passenger_count.
- dim_date: generated, 2025-01-01 to 2025-03-31, with day_of_week, is_weekend and month.
- dim_payment_type, dim_vendor, dim_ratecode: dbt seeds from the TLC data dictionary (docs/02-data-sources.md). A null key in the source maps to -1 with the name Unknown.
- dim_location: not now. It needs the TLC zone lookup file. Later option; the fact already carries both location ids.
- mart_daily_revenue is built from fct_trips: pickup_date, revenue, trip_count.
- A2 becomes: staged total = fct_trips total = mart revenue total, within 0.01.
- Staging casts total_amount to DECIMAL(12,2) so sums are exact. The mart revenue keeps that type.
Consequences: More models and tests than a single mart. Dimension integrity is tested (no fact key without a dimension row). The three-way reconciliation catches a join that drops or doubles trips.
Built after the Prefect orchestration; the mart was first built from staging, then repointed to fct_trips. The star schema tests are enabled. Result for Jan to Mar: staged, fact and mart totals are all 3,395,290.56 (146,475 trips, 90 days). Build notes: dim_date uses ISO day_of_week (1 Monday, 7 Sunday). The seeds add -1 Unknown to the TLC values. `dbt seed` now runs before `dbt run` (make transform, the plain entry point and the flows).
