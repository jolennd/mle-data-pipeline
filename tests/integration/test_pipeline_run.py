import sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from conftest import IN_RANGE_DAYS, synthetic_table

pytestmark = pytest.mark.integration


class FakeFetch:
    """Stands in for the network: writes the synthetic partition."""

    def __init__(self):
        self.calls = 0

    def __call__(self, url, dest):
        self.calls += 1
        pq.write_table(synthetic_table(), dest)


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_CONN", f"duckdb:///{tmp_path / 'warehouse.duckdb'}")
    monkeypatch.setenv("SOURCE_BASE_URL", "https://example.test/trip-data")
    monkeypatch.setenv("SOURCE_FILE_PATTERN", "green_tripdata_{partition}.parquet")
    monkeypatch.setenv("PARTITIONS", "2025-01")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("PROCESSED_DIR", str(tmp_path / "processed"))
    monkeypatch.setenv(
        "PATH", f"{Path(sys.executable).parent}:{__import__('os').environ['PATH']}"
    )
    return tmp_path


def test_pipeline_run_end_to_end(env):
    from data_pipeline.pipeline import run_pipeline

    run_pipeline("2025-01", fetch=FakeFetch())
    table = pq.read_table(env / "processed" / "daily_revenue.parquet")
    assert table.num_rows == IN_RANGE_DAYS


def test_pipeline_rerun_gives_same_output(env):
    from data_pipeline.pipeline import run_pipeline

    fetch = FakeFetch()
    run_pipeline("2025-01", fetch=fetch)
    first = pq.read_table(env / "processed" / "daily_revenue.parquet")
    run_pipeline("2025-01", fetch=fetch)
    second = pq.read_table(env / "processed" / "daily_revenue.parquet")
    assert first.equals(second)
    assert fetch.calls == 1  # the staged file is reused


def test_pipeline_stops_at_first_failing_step(env, monkeypatch):
    from data_pipeline import pipeline

    ran = []
    monkeypatch.setattr(pipeline, "load_partition", lambda p: ran.append("load"))
    monkeypatch.setattr(pipeline, "run_transform", lambda: ran.append("transform"))
    monkeypatch.setattr(pipeline, "export_mart", lambda: ran.append("export"))

    def broken(url, dest):
        raise ConnectionError("no route")

    with pytest.raises(Exception, match="download"):
        pipeline.run_pipeline("2025-01", fetch=broken)
    assert ran == []

    ran.clear()
    monkeypatch.setattr(pipeline, "download_partition", lambda p, fetch=None: None)

    def failing_transform():
        raise RuntimeError("transform failed")

    monkeypatch.setattr(pipeline, "run_transform", failing_transform)
    with pytest.raises(RuntimeError, match="transform failed"):
        pipeline.run_pipeline("2025-01")
    assert ran == ["load"]  # export never ran


def test_pipeline_cli(env, monkeypatch):
    from click.testing import CliRunner

    from data_pipeline import pipeline

    monkeypatch.setattr(pipeline, "run_pipeline", lambda partition, fetch=None: None)
    assert CliRunner().invoke(pipeline.main, ["2025-01"]).exit_code == 0
