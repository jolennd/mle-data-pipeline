import pytest

pytestmark = pytest.mark.integration

ROW_FLOOR = 5

RAW_COLUMNS = {
    "VendorID",
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "RatecodeID",
    "ehail_fee",
    "total_amount",
    "loaded_at",
    "source_partition",
}
STG_COLUMNS = {
    "vendor_id",
    "pickup_datetime",
    "dropoff_datetime",
    "pickup_date",
    "pickup_location_id",
    "dropoff_location_id",
    "ratecode_id",
    "total_amount",
}
MART_COLUMNS = {"pickup_date", "revenue"}


def columns_of(con, table):
    rows = con.execute(
        "select column_name from information_schema.columns where table_name = ?",
        [table],
    ).fetchall()
    return {r[0] for r in rows}


def schema_of(con, table):
    """Raw, staging and mart may sit in different schemas; find the one table by name."""
    rows = con.execute(
        "select table_schema from information_schema.tables where table_name = ?",
        [table],
    ).fetchall()
    assert len(rows) == 1, f"{table} must exist exactly once, found {rows}"
    return f"{rows[0][0]}.{table}"


def test_tables_exist_with_columns(built_db):
    assert RAW_COLUMNS <= columns_of(built_db, "raw_green_trips")
    assert STG_COLUMNS <= columns_of(built_db, "stg_green_trips")
    assert MART_COLUMNS <= columns_of(built_db, "mart_daily_revenue")
    assert "ehail_fee" not in columns_of(built_db, "stg_green_trips")


def test_key_unique(built_db):
    mart = schema_of(built_db, "mart_daily_revenue")
    rows, days = built_db.execute(
        f"select count(*), count(distinct pickup_date) from {mart}"
    ).fetchone()
    assert rows == days


def test_event_time_and_loaded_at_present(built_db):
    raw = schema_of(built_db, "raw_green_trips")
    stg = schema_of(built_db, "stg_green_trips")
    nulls = built_db.execute(
        f"select count(*) filter (where loaded_at is null), "
        f"count(*) filter (where source_partition is null), "
        f"count(*) filter (where lpep_pickup_datetime is null) from {raw}"
    ).fetchone()
    assert nulls == (0, 0, 0)
    (stg_nulls,) = built_db.execute(
        f"select count(*) filter (where pickup_datetime is null or pickup_date is null) "
        f"from {stg}"
    ).fetchone()
    assert stg_nulls == 0
    (source,) = built_db.execute(
        f"select distinct source_partition from {raw}"
    ).fetchone()
    assert source == "green_tripdata_2025-01.parquet"


def test_row_counts_above_floor(built_db, expected):
    raw = schema_of(built_db, "raw_green_trips")
    mart = schema_of(built_db, "mart_daily_revenue")
    (raw_rows,) = built_db.execute(f"select count(*) from {raw}").fetchone()
    (mart_rows,) = built_db.execute(f"select count(*) from {mart}").fetchone()
    assert raw_rows == expected["raw_rows"]
    assert raw_rows >= ROW_FLOOR
    assert mart_rows == expected["mart_days"]
