| Req | Requirement | Phase | Test name | Status |
|---|---|---|---|---|
| R1 | Download the monthly Green Taxi Parquet files for the requested months into the git-ignored staging folder, skipping files that exist, and check each is readable | 2 | test_download_writes_staged_files | open |
| R2 | A failed download or a missing month raises | 2 | test_download_failure_is_loud | open |
| R3 | Download links are built from config (host, file name pattern, months, staging folder), never hard-coded | 2 | test_download_urls_built_from_config | open |
| R4 | Raw, staging and mart tables exist with the contract columns (raw has loaded_at and source_partition) | 2 | test_tables_exist_with_columns | open |
| R5 | Mart has one row per pickup date (the key is unique) | 2 | test_key_unique | open |
| R6 | Loading a month twice gives the same rows (delete the month, then insert, in one transaction) | 2 | test_load_is_idempotent | open |
| R7 | A changed source schema fails the load | 2 | test_schema_drift_fails | open |
| R8 | A1: raw row count per month equals the source Parquet row count | 2 | test_raw_row_count_matches_source | open |
| R9 | Staging keeps pickup dates >= 2025-01-01 and < 2025-04-01, assigned by pickup date and not by source file (ADR 2) | 2 | test_staging_date_range | open |
| R10 | Rows outside the range are counted and logged, never dropped silently (ADR 2) | 2 | test_excluded_rows_are_counted_and_logged | open |
| R11 | Revenue is total_amount summed as is, negatives included (ADR 1) | 2 | test_revenue_includes_negative_amounts | open |
| R12 | A2: staged total_amount total = mart revenue total, within 0.01 (first check to fail). Becomes staged = fact = mart when the mart is repointed to fct_trips (ADR 13) | 2 | test_mart_totals_match_source | open |
| R13 | Data rules in staging and mart (not null, unique, accepted range) each have a dbt data test | 2 | make transform-test | open |
| R14 | The mart is exported to data/processed/daily_revenue.parquet; a rerun overwrites it with the same content | 2 | test_export_writes_processed_file | open |
| R15 | A plain entry point runs download, load, transform and export for one month and stops at the first failing step | 2 | test_pipeline_run_end_to_end | open |
| R16 | Findings from the exploration notebook are written to docs/02-data-sources.md | 2 | gate check by the reviewer | open |
| R17 | Connection read only from DB_CONN; no secret in the repo | 2, 3 | test_no_secret_in_flow_files | open |
| R18 | The flow takes one month (YYYY-MM) as its parameter and creates the expected tables | 3 | test_flow_creates_tables | open |
| R19 | Rerunning a month through the flow keeps the same counts | 3 | test_flow_rerun_is_idempotent | open |
| R20 | A failing step stops the steps after it and the run raises | 3 | test_failure_stops_downstream | open |
| R21 | The download task retries 3 times, 60 seconds apart | 3 | test_retry_count_is_configured | open |
| R22 | Tests never use the network | 2, 3 | test_no_network_in_tests | open |
| R23 | fct_trips has one row per trip: trip_id is unique (ADR 13) | 2 | test_fct_trip_id_unique | deferred |
| R24 | Every fact key has a row in its dimension; unknown source values map to -1 (ADR 13) | 2 | test_dims_referential_integrity | deferred |
| R25 | Staging casts total_amount to DECIMAL(12,2) (ADR 13) | 2 | test_total_amount_is_exact_decimal | open |
| R26 | db.connect() opens the duckdb file named by DB_CONN and fails loudly when it is unset or unsupported (ADR 14) | 2 | test_connect_reads_db_conn | open |
| R27 | source_partition holds the partition value, for example 2025-01 | 2 | test_event_time_and_loaded_at_present | open |
