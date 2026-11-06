Requirement ids (R1 to R27) are referenced in test docstrings. A1 and A2 are the acceptance numbers in [docs/00-project-brief.md](00-project-brief.md).

| Req | Requirement | Stage | Test name | Status |
|---|---|---|---|---|
| R1 | Download the monthly Green Taxi Parquet files for the requested months into the git-ignored staging folder, skipping files that exist, and check each is readable | data layer | test_download_writes_staged_files | done |
| R2 | A failed download or a missing month raises | data layer | test_download_failure_is_loud | done |
| R3 | Download links are built from config (host, file name pattern, months, staging folder), never hard-coded | data layer | test_download_urls_built_from_config | done |
| R4 | Raw, staging and mart tables exist with the contract columns (raw has loaded_at and source_partition) | data layer | test_tables_exist_with_columns | done |
| R5 | Mart has one row per pickup date (the key is unique) | data layer | test_key_unique | done |
| R6 | Loading a month twice gives the same rows (delete the month, then insert, in one transaction) | data layer | test_load_is_idempotent | done |
| R7 | A changed source schema fails the load | data layer | test_schema_drift_fails_and_keeps_old_rows, test_type_change_in_any_staged_column_fails | done |
| R8 | A1: raw row count per month equals the source Parquet row count | data layer | test_raw_row_count_matches_source | done |
| R9 | Staging keeps pickup dates >= 2025-01-01 and < 2025-04-01, assigned by pickup date and not by source file (ADR 2) | data layer | test_staging_date_range | done |
| R10 | Rows outside the range are counted and logged, never dropped silently (ADR 2) | data layer | test_excluded_rows_are_counted_and_logged | done |
| R11 | Revenue is total_amount summed as is, negatives included (ADR 1) | data layer | test_revenue_includes_negative_amounts | done |
| R12 | A2: staged total_amount total = mart revenue total, within 0.01 (first check to fail). Becomes staged = fact = mart when the mart is repointed to fct_trips (ADR 13) | data layer | test_mart_totals_match_source | done |
| R13 | Data rules in staging and mart (not null, unique, accepted range) each have a dbt data test | data layer | make transform-test | done |
| R14 | The mart is exported to data/processed/daily_revenue.parquet; a rerun overwrites it with the same content | data layer | test_export_writes_processed_file | done |
| R15 | A plain entry point runs download, load, transform and export for one month and stops at the first failing step | data layer | test_pipeline_run_end_to_end | done |
| R16 | Findings from the exploration notebook are written to docs/02-data-sources.md | data layer | manual review | done |
| R17 | Connection read only from DB_CONN; no secret in the repo | data layer, orchestration | test_no_secret_in_flow_files | done |
| R18 | The flow takes one month (YYYY-MM) as its parameter and creates the expected tables | orchestration | test_flow_creates_tables | done |
| R19 | Rerunning a month through the flow keeps the same counts | orchestration | test_flow_rerun_is_idempotent | done |
| R20 | A failing step stops the steps after it and the run raises | orchestration | test_failure_stops_downstream | done |
| R21 | The download task retries 3 times, 60 seconds apart | orchestration | test_retry_count_is_configured | done |
| R22 | Tests never use the network | data layer, orchestration | test_no_network_in_tests | done |
| R23 | fct_trips has one row per trip: trip_id is unique (ADR 13) | data layer | test_fct_trip_id_unique | done |
| R24 | Every fact key has a row in its dimension; unknown source values map to -1 (ADR 13) | data layer | test_dims_referential_integrity | done |
| R25 | Staging casts total_amount to DECIMAL(12,2) (ADR 13) | data layer | test_total_amount_is_exact_decimal | done |
| R26 | db.connect() opens the duckdb file named by DB_CONN and fails loudly when it is unset or unsupported (ADR 14) | data layer | test_connect_reads_db_conn | done |
| R27 | source_partition holds the partition value, for example 2025-01 | data layer | test_event_time_and_loaded_at_present (changed in 28e41d3: raw keeps rows with no pickup time, so only those may lack the event time) | done |
