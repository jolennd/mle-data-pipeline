import sys
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
import pytest
from conftest import IN_RANGE_DAYS, synthetic_table
from prefect.testing.utilities import prefect_test_harness

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def _prefect_backend():
    with prefect_test_harness():
        yield


@pytest.fixture
def env(monkeypatch, tmp_path):
    db_file = tmp_path / "warehouse.duckdb"
    monkeypatch.setenv("DB_CONN", f"duckdb:///{db_file}")
    monkeypatch.setenv("SOURCE_BASE_URL", "https://example.test/trip-data")
    monkeypatch.setenv("SOURCE_FILE_PATTERN", "green_tripdata_{partition}.parquet")
    monkeypatch.setenv("PARTITIONS", "2025-01,2025-02,2025-03")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(tmp_path / "processed"))
    monkeypatch.setenv(
        "PATH", f"{Path(sys.executable).parent}:{__import__('os').environ['PATH']}"
    )

    def fake_fetch(url, dest):
        pq.write_table(synthetic_table(), dest)

    monkeypatch.setattr("data_pipeline.ingest.download.http_fetch", fake_fetch)
    return db_file


def _count(db_file, table):
    con = duckdb.connect(str(db_file), read_only=True)
    try:
        return con.execute(f"select count(*) from {table}").fetchone()[0]
    finally:
        con.close()


def _tables(db_file):
    con = duckdb.connect(str(db_file), read_only=True)
    try:
        return {r[0] for r in con.execute("show tables").fetchall()}
    finally:
        con.close()


def test_flow_creates_tables(env, tmp_path):
    from flows.green_trips import green_trips_flow

    green_trips_flow("2025-01")
    assert {"raw_green_trips", "stg_green_trips", "daily_revenue"} <= _tables(env)
    table = pq.read_table(tmp_path / "processed" / "daily_revenue.parquet")
    assert table.num_rows == IN_RANGE_DAYS


def test_flow_rerun_is_idempotent(env):
    from flows.green_trips import green_trips_flow

    green_trips_flow("2025-01")
    first = {t: _count(env, t) for t in ("raw_green_trips", "daily_revenue")}
    green_trips_flow("2025-01")
    second = {t: _count(env, t) for t in ("raw_green_trips", "daily_revenue")}
    assert first == second


def test_failure_stops_downstream(env, monkeypatch):
    from flows.green_trips import green_trips_flow

    from data_pipeline import pipeline

    ran = []
    monkeypatch.setattr(pipeline, "load_partition", lambda p: ran.append("load"))

    def broken():
        raise RuntimeError("transform failed")

    monkeypatch.setattr(pipeline, "run_transform", broken)
    monkeypatch.setattr(pipeline, "export_mart", lambda: ran.append("export"))
    with pytest.raises(Exception, match="transform failed"):
        green_trips_flow("2025-01")
    assert ran == ["load"]


def test_partition_is_validated(env):
    from flows.green_trips import green_trips_flow

    for bad in ("2025-1", "January", "2025-13", "2024-12", ""):
        with pytest.raises(Exception, match="partition"):
            green_trips_flow(bad)


def test_run_name_uses_partition(env):
    from flows.green_trips import green_trips_flow

    assert green_trips_flow.flow_run_name == "green-trips-{partition}"
    state = green_trips_flow("2025-01", return_state=True)
    assert state.is_completed()


def test_parent_flow_runs_months_in_order(env, monkeypatch):
    from flows import green_trips

    order = []
    monkeypatch.setattr(
        green_trips, "green_trips_flow", lambda partition: order.append(partition)
    )
    green_trips.green_trips_all()
    assert order == ["2025-01", "2025-02", "2025-03"]
