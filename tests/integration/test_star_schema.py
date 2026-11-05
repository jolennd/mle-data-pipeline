import pytest
from contract_helpers import columns_of, schema_of

pytestmark = pytest.mark.integration

FCT_COLUMNS = {
    "trip_id",
    "pickup_date",
    "payment_type",
    "vendor_id",
    "ratecode_id",
    "pickup_location_id",
    "dropoff_location_id",
    "total_amount",
    "fare_amount",
    "tip_amount",
    "trip_distance",
    "passenger_count",
}
DIM_COLUMNS = {
    "dim_date": {"pickup_date", "day_of_week", "is_weekend", "month"},
    "dim_payment_type": {"payment_type"},
    "dim_vendor": {"vendor_id"},
    "dim_ratecode": {"ratecode_id"},
}


def test_star_tables_exist_with_columns(built_db):
    assert FCT_COLUMNS <= columns_of(built_db, "fct_trips")
    for table, columns in DIM_COLUMNS.items():
        assert columns <= columns_of(built_db, table), table


def test_fct_trip_id_unique(built_db):
    fct = schema_of(built_db, "fct_trips")
    rows, ids, nulls = built_db.execute(
        f"select count(*), count(distinct trip_id), "
        f"count(*) filter (where trip_id is null) from {fct}"
    ).fetchone()
    assert rows == ids
    assert nulls == 0


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
    (unknown,) = built_db.execute(
        f"select count(*) from {fct} where payment_type = -1 and ratecode_id = -1"
    ).fetchone()
    assert unknown == 1
    (days,) = built_db.execute(
        f"select count(*) from {schema_of(built_db, 'dim_date')}"
    ).fetchone()
    assert days == 90  # 2025-01-01 to 2025-03-31


def test_totals_match_across_three_tables(built_db, expected):
    """A2 after the repoint: staged total = fact total = mart revenue total."""
    totals = {}
    for table, column in (
        ("stg_green_trips", "total_amount"),
        ("fct_trips", "total_amount"),
        ("mart_daily_revenue", "revenue"),
    ):
        name = schema_of(built_db, table)
        (totals[table],) = built_db.execute(
            f"select sum({column}) from {name}"
        ).fetchone()
    stg, fct, mart = (float(v) for v in totals.values())
    assert abs(stg - fct) <= 0.01
    assert abs(fct - mart) <= 0.01


def test_fare_and_tip_totals_match_staging(built_db):
    stg = schema_of(built_db, "stg_green_trips")
    fct = schema_of(built_db, "fct_trips")
    for column in ("fare_amount", "tip_amount"):
        (stg_sum,) = built_db.execute(f"select sum({column}) from {stg}").fetchone()
        (fct_sum,) = built_db.execute(f"select sum({column}) from {fct}").fetchone()
        assert abs(float(stg_sum) - float(fct_sum)) <= 0.01, column
