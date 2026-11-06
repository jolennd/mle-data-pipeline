# ADR 17: Flow shape and retries
Status: accepted
Context: Prefect wraps the plain entry point in an orchestrator. DuckDB allows one writer, and the boundary days of a month are complete only after every month is loaded (ADR 2).
Decision: One flow per month (partition YYYY-MM, checked against PARTITIONS, run name green-trips-{partition}) with tasks download, load, transform, export that call the functions pipeline.py calls. A parent flow runs the configured months one after another. Only download retries (3 times, 60 seconds apart); load, transform and export are deterministic and do not. The demo schedule is monthly (06:00 on day 1).
Consequences: No parallel months. A failed task stops the tasks after it and the run raises. Settings still come only from the environment, so flows are started through make (which loads .env).
Test and config notes: after the red commit, the contract test only corrected a table name (mart_daily_revenue) and import order; no assertion was weakened. pytest `pythonpath` in pyproject.toml now includes the project root so tests can import `flows`.
