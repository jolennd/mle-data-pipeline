import pytest
from contract_helpers import columns_of, schema_of

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
    "payment_type",
    "total_amount",
    "is_total_amount_missing",
}
MART_COLUMNS = {"pickup_date", "revenue", "trip_count"}


def test_tables_exist_with_columns(built_db):
    assert RAW_COLUMNS <= columns_of(built_db, "raw_green_trips")
    assert STG_COLUMNS <= columns_of(built_db, "stg_green_trips")
    assert "ehail_fee" not in columns_of(built_db, "stg_green_trips")
    assert MART_COLUMNS <= columns_of(built_db, "mart_daily_revenue")


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
    assert source == "2025-01"


def test_row_counts_above_floor(built_db, expected):
    counts = {}
    for table in ("raw_green_trips", "stg_green_trips", "mart_daily_revenue"):
        name = schema_of(built_db, table)
        (counts[table],) = built_db.execute(f"select count(*) from {name}").fetchone()
    assert counts["raw_green_trips"] == expected["raw_rows"]
    assert counts["raw_green_trips"] >= ROW_FLOOR
    assert counts["stg_green_trips"] == expected["in_range_rows"]
    assert counts["mart_daily_revenue"] == expected["mart_days"]


def test_mart_totals_match_source(built_db, expected):
    """A2: staged total_amount total equals mart revenue total, within 0.01."""
    stg = schema_of(built_db, "stg_green_trips")
    mart = schema_of(built_db, "mart_daily_revenue")
    (staged,) = built_db.execute(f"select sum(total_amount) from {stg}").fetchone()
    (revenue, trips) = built_db.execute(
        f"select sum(revenue), sum(trip_count) from {mart}"
    ).fetchone()
    assert abs(float(staged) - float(revenue)) <= 0.01
    assert abs(float(staged) - expected["in_range_total"]) <= 0.01
    assert trips == expected["in_range_rows"]
