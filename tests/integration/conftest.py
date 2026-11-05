"""Builds one small database from a synthetic partition. No real data, no network."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
PARTITION = "2025-01"

# (pickup, total_amount, payment_type, vendor_id, ratecode_id).
# One row is before the range, one is in February, one has unknown payment and rate code,
# one has no pickup time and one has no amount.
SYNTHETIC_TRIPS = [
    (datetime(2024, 12, 31, 23, 50), 10.0, 1, 2, 1),
    (datetime(2025, 1, 1, 0, 5), 20.0, 1, 2, 1),
    (datetime(2025, 1, 1, 8, 0), 15.5, 2, 2, 1),
    (datetime(2025, 1, 1, 22, 30), -5.0, 2, 2, 1),
    (datetime(2025, 1, 2, 9, 0), 12.25, None, 1, None),
    (datetime(2025, 1, 2, 18, 45), 30.0, 1, 1, 2),
    (datetime(2025, 1, 3, 12, 0), 8.0, 3, 2, 1),
    (datetime(2025, 1, 31, 23, 59), 41.0, 1, 2, 5),
    (datetime(2025, 2, 2, 7, 15), 9.75, 4, 6, 1),
    (None, 7.0, 1, 2, 1),  # no pickup time: excluded from staging, counted
    (datetime(2025, 1, 3, 15, 0), None, 1, 2, 1),  # no amount: kept and flagged
]
RANGE_START = datetime(2025, 1, 1)
RANGE_END = datetime(2025, 4, 1)
IN_RANGE = [
    t for t in SYNTHETIC_TRIPS if t[0] is not None and RANGE_START <= t[0] < RANGE_END
]
IN_RANGE_DAYS = len({t[0].date() for t in IN_RANGE})  # Jan 1, 2, 3, 31 and Feb 2


def synthetic_table() -> pa.Table:
    n = len(SYNTHETIC_TRIPS)
    pickups = [t[0] for t in SYNTHETIC_TRIPS]
    return pa.table(
        {
            "VendorID": pa.array([t[3] for t in SYNTHETIC_TRIPS], pa.int32()),
            "lpep_pickup_datetime": pa.array(pickups, pa.timestamp("us")),
            "lpep_dropoff_datetime": pa.array(pickups, pa.timestamp("us")),
            "store_and_fwd_flag": ["N"] * n,
            "RatecodeID": pa.array([t[4] for t in SYNTHETIC_TRIPS], pa.int64()),
            "PULocationID": pa.array([75] * n, pa.int32()),
            "DOLocationID": pa.array([166] * n, pa.int32()),
            "passenger_count": pa.array([1] * n, pa.int64()),
            "trip_distance": [1.5] * n,
            "fare_amount": [5.0] * n,
            "extra": [0.0] * n,
            "mta_tax": [0.5] * n,
            "tip_amount": [0.0] * n,
            "tolls_amount": [0.0] * n,
            "ehail_fee": pa.array([None] * n, pa.float64()),
            "improvement_surcharge": [1.0] * n,
            "total_amount": [t[1] for t in SYNTHETIC_TRIPS],
            "payment_type": pa.array([t[2] for t in SYNTHETIC_TRIPS], pa.int64()),
            "trip_type": pa.array([1] * n, pa.int64()),
            "congestion_surcharge": [0.0] * n,
            "cbd_congestion_fee": [0.0] * n,
        }
    )


@pytest.fixture(scope="module")
def built_db(tmp_path_factory):
    """Load one partition, run the transforms, return a read connection."""
    tmp = tmp_path_factory.mktemp("contract")
    staging = tmp / "raw"
    staging.mkdir()
    pq.write_table(synthetic_table(), staging / f"green_tripdata_{PARTITION}.parquet")
    db_file = tmp / "warehouse.duckdb"

    mp = pytest.MonkeyPatch()
    mp.setenv("DB_CONN", f"duckdb:///{db_file}")
    mp.setenv("SOURCE_BASE_URL", "https://example.test/trip-data")
    mp.setenv("SOURCE_FILE_PATTERN", "green_tripdata_{partition}.parquet")
    mp.setenv("PARTITIONS", PARTITION)
    mp.setenv("STAGING_DIR", str(staging))
    mp.setenv("PROCESSED_DIR", str(tmp / "processed"))
    mp.setenv(
        "PATH", f"{Path(sys.executable).parent}:{__import__('os').environ['PATH']}"
    )
    try:
        from data_pipeline.ingest.load import load_partition

        load_partition(PARTITION)
        for command in ("seed", "run"):
            subprocess.run(
                [sys.executable, str(ROOT / "transform" / "dbt_env.py"), command],
                check=True,
                cwd=ROOT,
            )
        con = duckdb.connect(str(db_file), read_only=True)
        yield con
        con.close()
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def expected():
    return {
        "raw_rows": len(SYNTHETIC_TRIPS),
        "in_range_rows": len(IN_RANGE),
        "excluded_null_pickup": sum(1 for t in SYNTHETIC_TRIPS if t[0] is None),
        "excluded_out_of_range": sum(
            1 for t in SYNTHETIC_TRIPS if t[0] is not None and t not in IN_RANGE
        ),
        "null_total_rows": sum(1 for t in IN_RANGE if t[1] is None),
        "mart_days": IN_RANGE_DAYS,
        "in_range_total": sum(t[1] for t in IN_RANGE if t[1] is not None),
    }
