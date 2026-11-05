# ADR 14: db.py becomes a small connect() helper
Status: accepted
Context: db.py built a SQLAlchemy engine, but the project uses DuckDB and has no duckdb-engine dependency. Nothing imports it yet. The loader and dbt must reach the same file from the same value.
Decision: db.py is replaced by connect(read_only=False), which reads DB_CONN through require_env and returns a duckdb connection. It accepts the duckdb:/// form: duckdb:///relative/path.duckdb is relative to the working directory, duckdb:////absolute/path.duckdb is absolute. Any other scheme raises. transform/dbt_env.py applies the same rule to DB_CONN, so both open the same file. The SQLAlchemy fixture in tests/conftest.py is removed.
Consequences: No sqlalchemy import in project code. A change of database later needs a new ADR. Shared file: needs approval.
