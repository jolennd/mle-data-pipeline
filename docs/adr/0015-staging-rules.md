# ADR 15: Staging rules for rows and columns
Status: accepted
Context: Building staging and checking totals needs explicit rules for duplicates, odd rows and unused columns. January findings are in docs/02-data-sources.md.
Decision:
- No natural key and no exact duplicate rows in January, so stg_green_trips is not deduplicated. A month with exact duplicates is a stop-and-report case (ADR 13 trip_id).
- ehail_fee is kept in raw and dropped from staging (always null in January).
- Rows with no pickup time are excluded from staging. Rows with a pickup date outside 2025-01-01 to 2025-03-31 are excluded (ADR 2). Both are counted and logged per partition (raw, staged, excluded) and raw equals staged plus excluded.
- A null total_amount is kept and flagged with is_total_amount_missing. It adds nothing to revenue. Negative amounts are kept (ADR 1).
- Staging and mart tables are created in the main schema of the single DuckDB file (dbt schema default main in transform/profiles.yml), so raw, staging and mart share one place. The range dates are dbt vars in dbt_project.yml.
- Staging has no joins to tables that change over time, so the point-in-time test (test_no_future_joins) is skipped. It returns when dimensions are added (ADR 13).
Consequences: Every excluded row is visible in the log. A rule change needs a new ADR and a changed test.
