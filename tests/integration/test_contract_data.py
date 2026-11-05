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
}
FCT_COLUMNS = {
    "trip_id",
    "pickup_date",
    "payment_type",
    "vendor_id",
    "ratecode_id",
    "pickup_location_id",
    "dropoff_location_id",
    "total_amount",
    "trip_distance",
    "passenger_count",
}
DIM_COLUMNS = {
    "dim_date": {"pickup_date", "day_of_week", "is_weekend", "month"},
    "dim_payment_type": {"payment_type"},
    "dim_vendor": {"vendor_id"},
    "dim_ratecode": {"ratecode_id"},
}
MART_COLUMNS = {"pickup_date", "revenue", "trip_count"}


def test_tables_exist_with_columns(built_db):
    assert RAW_COLUMNS <= columns_of(built_db, "raw_green_trips")
    assert STG_COLUMNS <= columns_of(built_db, "stg_green_trips")
    assert "ehail_fee" not in columns_of(built_db, "stg_green_trips")
    assert FCT_COLUMNS <= columns_of(built_db, "fct_trips")
    for table, columns in DIM_COLUMNS.items():
        assert columns <= columns_of(built_db, table), table
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
    for table in (
        "raw_green_trips",
        "stg_green_trips",
        "fct_trips",
        "mart_daily_revenue",
    ):
        name = schema_of(built_db, table)
        (counts[table],) = built_db.execute(f"select count(*) from {name}").fetchone()
    assert counts["raw_green_trips"] == expected["raw_rows"]
    assert counts["raw_green_trips"] >= ROW_FLOOR
    assert counts["stg_green_trips"] == expected["in_range_rows"]
    assert counts["fct_trips"] == expected["in_range_rows"]
    assert counts["mart_daily_revenue"] == expected["mart_days"]


def test_dims_referential_integrity(built_db):
    fct = schema_of(built_db, "fct_trips")
    links = {
        "dim_date": "pickup_date",
        "dim_payment_type": "payment_type",
        "dim_vendor": "vendor_id",
        "dim_ratecode": "ratecode_id",
    }
    for dim, key in links.items():
        name = schema_of(built_db, dim)
        (orphans,) = built_db.execute(
            f"select count(*) from {fct} f left join {name} d on f.{key} = d.{key} "
            f"where d.{key} is null"
        ).fetchone()
        assert orphans == 0, f"{dim}: {orphans} fact rows without a dimension row"
    # A null in the source maps to -1 (Unknown), never to a null key.
    (unknown_payment,) = built_db.execute(
        f"select count(*) from {fct} where payment_type = -1 and ratecode_id = -1"
    ).fetchone()
    assert unknown_payment == 1
    (days,) = built_db.execute(
        f"select count(*) from {schema_of(built_db, 'dim_date')}"
    ).fetchone()
    assert days == 90  # 2025-01-01 to 2025-03-31
