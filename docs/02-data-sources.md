| Source | Location | Refresh | Owner | Notes |
|---|---|---|---|---|
| NYC Green Taxi trip records, Parquet, one file per month (2025-01, 2025-02, 2025-03) | NYC Taxi and Limousine Commission (TLC) public trip data. Base URL and file name pattern live in config, not in code. Pattern `green_tripdata_YYYY-MM.parquet`. Base URL `https://d37ci6vzurychx.cloudfront.net/trip-data` checked 2026-11-05: `curl -I` for `green_tripdata_2025-01.parquet` returned HTTP/2 200, 1,178,451 bytes | Published monthly by the source. This project is a fixed backfill of Jan to Mar 2025, no live refresh | NYC TLC | Columns the output needs: `lpep_pickup_datetime` (sets the day) and `total_amount` (revenue, negatives kept). Files can contain rows with pickup dates outside their own month (ADR 2). Local copy is saved to the git-ignored `data/raw/` staging folder. |

## Exploration findings
Notebook: `notebooks/02_explore_green_trips.ipynb`, read file `green_tripdata_2025-01.parquet` (checked 2026-11-05). Only January is explored so far. Feb and Mar counts are read when those files are loaded.
- Columns: 21, names match the brief. `lpep_pickup_datetime` and `lpep_dropoff_datetime` are TIMESTAMP, `total_amount` is DOUBLE. Others: VendorID, store_and_fwd_flag, RatecodeID, PULocationID, DOLocationID, passenger_count, trip_distance, fare_amount, extra, mta_tax, tip_amount, tolls_amount, ehail_fee, improvement_surcharge, payment_type, trip_type, congestion_surcharge, cbd_congestion_fee.
- Row count 2025-01 (expected value for A1): 48,326.
- Missing values: `lpep_pickup_datetime` 0, `total_amount` 0, `ehail_fee` 48,326 (all null, column carries no information).
- `total_amount`: min -114.0, max 371.4, sum 1,093,822.36. 153 negative rows (ADR 1 keeps them), 33 zero rows.
- `lpep_pickup_datetime`: min 2024-12-25 23:13:15, max 2025-02-05 18:46:24. 6 rows have pickups before 2025-01-01 (2024-12-25: 1, 2024-12-29: 1, 2024-12-31: 4), outside Jan to Mar 2025, so staging excludes them (ADR 2). 37 rows have pickups on 2025-02-01 to 2025-02-05, outside the file's month but inside the range, so staging keeps them and they count on their pickup day.
- Natural key: none. No id column, and all 48,326 rows are distinct on all columns. Staging is not deduplicated (ADR needed in step 8).
- No stop condition hit: an event time column exists and the key question is answered.

What needs cleaning, and where it goes:
- Rows with pickup before 2025-01-01: excluded in staging, counted and logged (data test `test_staging_date_range`, `test_excluded_rows_are_counted_and_logged`).
- Negative and zero `total_amount`: kept (ADR 1, `test_revenue_includes_negative_amounts`).
- No null pickup or null `total_amount` in January: the flag and exclude rules still get a test on a fixture, since other months may differ.
- `ehail_fee` all null: carried through, ignored by the mart. Decide in the step 8 ADR whether staging drops it.

## Decisions (phase 2)
- Partition format: YYYY-MM.
- Natural key: none (confirmed in January: no id column, no exact duplicates). If staging is not deduplicated, an ADR says why.
- Staging rename map: lpep_pickup_datetime to pickup_datetime, lpep_dropoff_datetime to dropoff_datetime, PULocationID to pickup_location_id, DOLocationID to dropoff_location_id, VendorID to vendor_id, RatecodeID to ratecode_id. total_amount keeps its name (A2). Staging adds pickup_date. Other columns: snake_case, finalized after exploration.
- Impossible values: flag and keep. Null total_amount: row kept with a flag, adds nothing to revenue (A2 treats nulls the same on both sides). Null pickup time: excluded from staging, counted and logged like the date-range rows.
- Export: data/processed/daily_revenue.parquet.
- ehail_fee: kept in raw, dropped from staging (entirely null in January). To be recorded in the step 8 ADR.
- source_partition holds the partition value, for example 2025-01, the same value as the partition parameter.
- Staging casts total_amount to DECIMAL(12,2) so sums are exact.
- Model: star schema under the daily mart (ADR 13). Dimension keys for a null in the source are -1 (Unknown).

## Data dictionary
Source of the dimension seeds: TLC Data Dictionary, LPEP Trip Records (green), dated March 18, 2025. URL: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_green.pdf. Fetched and read 2026-11-05.
- VendorID: 1 Creative Mobile Technologies, LLC; 2 Curb Mobility, LLC; 6 Myle Technologies Inc.
- RatecodeID: 1 Standard rate; 2 JFK; 3 Newark; 4 Nassau or Westchester; 5 Negotiated fare; 6 Group ride; 99 Null/unknown.
- payment_type: 0 Flex Fare trip; 1 Credit card; 2 Cash; 3 No charge; 4 Dispute; 5 Unknown; 6 Voided trip.

## More findings (January file, checked 2026-11-05)
- Negative amounts: all 153 negative rows have a positive twin (same pickup time, same pickup location, opposite amount; 150 also match the dropoff location). Summing total_amount as is nets the reversals out.
- 1,836 rows have a null payment_type. Their amounts are valid (sum 56,589.29), so they are kept and get the dimension key -1 (Unknown). The same 1,836 rows also have a null ratecode_id and a null passenger_count.
- Payment types 3 and 4 are 430 rows and 1,724.45, about 0.16% of revenue (ADR 1).
- The fee columns do not always add up to total_amount (6,698 rows differ by more than 0.005). We use total_amount as published.
- No exact duplicate rows in January (ADR 13 stops and reports if a month has them).

