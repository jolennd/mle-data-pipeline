# Project brief
Kind: pipeline
Problem: Turn NYC Green Taxi trip records for Jan to Mar 2025 into a daily revenue table.
Users: data analysts and finance or operations stakeholders who need daily revenue for NYC Green Taxi trips, Jan to Mar 2025.
Constraints: runs locally, no cloud. Single DuckDB file, so loads run one month at a time. Data limited to Jan to Mar 2025. data/raw/ is git-ignored. No secrets in the repo; configuration read only from environment variables. Tests never use the network.

## Pipeline details
Source and refresh rate: NYC TLC Green Taxi monthly Parquet files, Jan to Mar 2025. Published monthly, fixed backfill, no live refresh.
Grain of the output (one row per what): one row per pickup date (from lpep_pickup_datetime).
Output tables or files: DuckDB tables raw_green_trips, stg_green_trips, fct_trips, dim_date, dim_payment_type, dim_vendor, dim_ratecode, mart_daily_revenue (ADR 13); file data/processed/daily_revenue.parquet. The deliverable stays revenue per day (pickup_date, revenue, trip_count).
Acceptance numbers (must reconcile to the source):
- A1: raw_green_trips row count per month equals the row count of the source Parquet file for that month. Verified values: 2025-01 48,326, 2025-02 46,621, 2025-03 51,539.
- A2: the total_amount sum over stg_green_trips equals the sum over fct_trips and equals the sum of mart_daily_revenue revenue, within 0.01. stg_green_trips keeps pickup dates >= 2025-01-01 and < 2025-04-01.
- Excluded rows (outside the range) are counted and logged, not silently dropped.
ELT. Load the Parquet files unchanged into raw_green_trips, then transform inside the database with dbt. Why: raw data stays untouched and re-readable, transforms are versioned SQL with tests, and rerunning a month gives the same result.
First check that fails when the output is wrong: A2, the totals reconciliation (mart revenue vs staged total_amount).
