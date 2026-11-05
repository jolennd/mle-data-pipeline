| Source | Location | Refresh | Owner | Notes |
|---|---|---|---|---|
| NYC Green Taxi trip records, Parquet, one file per month (2025-01, 2025-02, 2025-03) | NYC Taxi and Limousine Commission (TLC) public trip data. Base URL and file name pattern live in config, not in code. Pattern `green_tripdata_YYYY-MM.parquet`. Base URL `https://d37ci6vzurychx.cloudfront.net/trip-data` checked 2026-11-05: `curl -I` for `green_tripdata_2025-01.parquet` returned HTTP/2 200, 1,178,451 bytes | Published monthly by the source. This project is a fixed backfill of Jan to Mar 2025, no live refresh | NYC TLC | Columns the output needs: `lpep_pickup_datetime` (sets the day) and `total_amount` (revenue, negatives kept). Files can contain rows with pickup dates outside their own month (ADR 2). Local copy is saved to the git-ignored `data/raw/` staging folder. |

## Exploration findings
Not written yet. The phase 2 exploration notebook reads one staged file and records here: column types, missing values, value ranges for `lpep_pickup_datetime` and `total_amount`, the real row count per month (the expected values for A1), and what needs cleaning. Each finding becomes a data test or an ADR.

## Decisions (phase 2)
- Partition format: YYYY-MM.
- Natural key: none expected. The exploration step confirms it from the real file. If staging is not deduplicated, an ADR says why.
- Staging rename map: lpep_pickup_datetime to pickup_datetime, lpep_dropoff_datetime to dropoff_datetime, PULocationID to pickup_location_id, DOLocationID to dropoff_location_id, VendorID to vendor_id, RatecodeID to ratecode_id. total_amount keeps its name (A2). Staging adds pickup_date. Other columns: snake_case, finalized after exploration.
- Impossible values: flag and keep. Null total_amount: row kept with a flag, adds nothing to revenue (A2 treats nulls the same on both sides). Null pickup time: excluded from staging, counted and logged like the date-range rows.
- Export: data/processed/daily_revenue.parquet.
