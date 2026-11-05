import pytest
from contract_helpers import schema_of

pytestmark = pytest.mark.integration


def test_fct_trip_id_unique(built_db):
    fct = schema_of(built_db, "fct_trips")
    rows, ids, nulls = built_db.execute(
        f"select count(*), count(distinct trip_id), "
        f"count(*) filter (where trip_id is null) from {fct}"
    ).fetchone()
    assert rows == ids
    assert nulls == 0


def test_total_amount_is_exact_decimal(built_db):
    (dtype,) = built_db.execute(
        "select data_type from information_schema.columns "
        "where table_name = 'stg_green_trips' and column_name = 'total_amount'"
    ).fetchone()
    assert dtype == "DECIMAL(12,2)"


def test_totals_match_across_three_tables(built_db, expected):
    """A2: staged total = fact total = mart revenue total, within 0.01."""
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
    stg, fct, mart = (
        float(totals[t]) for t in ("stg_green_trips", "fct_trips", "mart_daily_revenue")
    )
    assert abs(stg - fct) <= 0.01
    assert abs(fct - mart) <= 0.01
    assert abs(stg - expected["in_range_total"]) <= 0.01
    (trips,) = built_db.execute(
        f"select sum(trip_count) from {schema_of(built_db, 'mart_daily_revenue')}"
    ).fetchone()
    assert trips == expected["in_range_rows"]
