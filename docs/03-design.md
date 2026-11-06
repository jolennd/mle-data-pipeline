# Design
## Components
1. Download: for one month, builds the file link from config, saves the Parquet file into the staging folder `data/raw/`, skips an existing file unless forced, checks the file is readable, raises on a failed download or a missing month. This is the only step that touches the network.
2. Load (ELT, raw): reads the staged file with the database's own file reader into `raw_green_trips`, keeping every row, with `loaded_at` and `source_partition` (the partition value, for example 2025-01, the same value as the flow parameter). Deletes the month and inserts it again in one transaction, so a rerun gives the same rows.
3. Transform, staging (dbt): `stg_green_trips` is typed and renamed (`total_amount` is DECIMAL(12,2)), drops `ehail_fee`, and keeps pickup dates >= 2025-01-01 and < 2025-04-01. The excluded rows are counted and logged.
4. Transform, star schema (dbt): `fct_trips` is one row per trip with `trip_id` (hash of `source_partition` and all source columns, unique). Keys: `pickup_date`, `payment_type`, `vendor_id`, `ratecode_id`, `pickup_location_id`, `dropoff_location_id`. Measures: `fare_amount`, `tip_amount`, `total_amount`, `trip_distance`, `passenger_count`. Dimensions: `dim_date` (generated, 2025-01-01 to 2025-03-31), and `dim_payment_type`, `dim_vendor`, `dim_ratecode` as dbt seeds from the TLC data dictionary. A null source key maps to -1 (Unknown). `dim_location` is a later option (ADR 13).
5. Transform, mart (dbt): `mart_daily_revenue` is built from `fct_trips`, one row per pickup date: `pickup_date`, `revenue` (sum of `total_amount`), `trip_count`. Data tests and the totals reconciliation (A2, across staging, fact and mart) run here.
6. Export: writes the mart to `data/processed/daily_revenue.parquet` with the database's own file writer. A rerun overwrites the file with the same content.
7. Plain entry point: runs download, load, transform and export in order for one month, and stops at the first failing step. It works without the orchestrator.
8. Prefect flow: wraps the same functions in the same order as tasks. The flow takes one month (YYYY-MM) as its parameter. It adds retries on the download task and no data logic.

## Handoffs
| From | To | Contract | Test |
|---|---|---|---|
| Source Parquet files | `raw_green_trips` | All source rows kept, plus `loaded_at` and `source_partition`. Row count per month equals the source file (A1). Schema drift fails the load. | `test_raw_row_count_matches_source`, `test_schema_drift_fails` |
| `raw_green_trips` | `stg_green_trips` | Typed and renamed, `total_amount` DECIMAL(12,2), no `ehail_fee`. Pickup dates in [2025-01-01, 2025-04-01). Excluded rows counted and logged. | `test_staging_date_range`, `test_excluded_rows_are_counted_and_logged` |
| `stg_green_trips` | `fct_trips` and dimensions | One row per trip, `trip_id` unique. Every fact key has a dimension row; a null source key maps to -1. Staged total equals fact total (A2). | `test_fct_trip_id_unique`, `test_dims_referential_integrity` |
| `fct_trips` | `mart_daily_revenue` | One row per pickup date, unique key. Revenue is `total_amount` summed as is. Staged, fact and mart totals are equal within 0.01 (A2). | `test_key_unique`, `test_totals_match_across_three_tables`, `test_revenue_includes_negative_amounts` |
| `mart_daily_revenue` | `data/processed/daily_revenue.parquet` | Same rows and columns as the mart. A rerun overwrites with the same content. | `test_export_writes_processed_file` |
| Plain entry point | Prefect flow | The flow calls the same functions in the same order. A month in, the same counts out on rerun. A failing step stops the rest. | `test_pipeline_run_end_to_end`, `test_flow_rerun_is_idempotent`, `test_failure_stops_downstream` |

## Tool choices (see stack.toml)
- database, duckdb: embedded single-file database, no server to run locally. One writer at a time, so loads run one month at a time.
- transform, dbt: versioned SQL models with built-in tests. The totals reconciliation (A2) runs here.
- orchestrator, prefect: Python-native flows for download, load, transform and export. The download task retries 3 times, 60 seconds apart. The flow takes one month (YYYY-MM) as its parameter. A failed step stops the run with a clear error.
- deploy, later: local only.
- monitoring, later: local only.
