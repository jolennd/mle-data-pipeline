import logging
from datetime import date

import pytest
from contract_helpers import schema_of

pytestmark = pytest.mark.integration


def test_staging_date_range(built_db):
    """Pickup date decides membership, not the source file (ADR 2)."""
    stg = schema_of(built_db, "stg_green_trips")
    low, high, outside = built_db.execute(
        f"select min(pickup_date), max(pickup_date), "
        f"count(*) filter (where pickup_date < date '2025-01-01' "
        f"or pickup_date >= date '2025-04-01') from {stg}"
    ).fetchone()
    assert outside == 0
    assert low == date(2025, 1, 1)
    assert high == date(2025, 2, 2)  # a February trip in the January file is kept


def test_excluded_rows_are_counted_and_logged(built_db, expected, caplog):
    from data_pipeline.ingest.counts import log_layer_counts

    with caplog.at_level(logging.INFO):
        counts = log_layer_counts("2025-01")
    assert counts["raw"] == expected["raw_rows"]
    assert counts["staged"] == expected["in_range_rows"]
    assert counts["excluded_out_of_range"] == expected["excluded_out_of_range"]
    assert counts["excluded_null_pickup"] == expected["excluded_null_pickup"]
    # Nothing is dropped silently: every raw row is staged or counted as excluded.
    excluded = counts["excluded_out_of_range"] + counts["excluded_null_pickup"]
    assert counts["raw"] == counts["staged"] + excluded
    assert "excluded" in caplog.text


def test_null_total_amount_is_flagged_and_kept(built_db, expected):
    stg = schema_of(built_db, "stg_green_trips")
    kept, flagged = built_db.execute(
        f"select count(*) filter (where total_amount is null), "
        f"count(*) filter (where is_total_amount_missing) from {stg}"
    ).fetchone()
    assert kept == expected["null_total_rows"] == flagged
    (wrong,) = built_db.execute(
        f"select count(*) from {stg} "
        f"where is_total_amount_missing != (total_amount is null)"
    ).fetchone()
    assert wrong == 0


def test_revenue_includes_negative_amounts(built_db):
    """ADR 1: negatives are summed as they are. 2025-01-01 is 20.0 + 15.5 - 5.0."""
    mart = schema_of(built_db, "mart_daily_revenue")
    (revenue,) = built_db.execute(
        f"select revenue from {mart} where pickup_date = date '2025-01-01'"
    ).fetchone()
    assert float(revenue) == 30.5


def test_total_amount_is_exact_decimal(built_db):
    (dtype,) = built_db.execute(
        "select data_type from information_schema.columns "
        "where table_name = 'stg_green_trips' and column_name = 'total_amount'"
    ).fetchone()
    assert dtype == "DECIMAL(12,2)"
