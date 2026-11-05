# ADR 2: Rows are assigned by pickup date and filtered in staging
Status: accepted
Context: Monthly source files can contain trips with pickup dates outside their month or outside Jan to Mar 2025.
Decision: The day of a trip is its lpep_pickup_datetime date, regardless of source file. raw_green_trips keeps all rows. stg_green_trips keeps pickup dates >= 2025-01-01 and < 2025-04-01. Excluded rows are counted and logged.
Consequences: Raw row counts match the source files (A1). Mart totals reconcile to the staged rows (A2). The exclusion count is visible in the run log.
