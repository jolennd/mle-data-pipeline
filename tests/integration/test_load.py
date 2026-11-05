import pyarrow.parquet as pq
import pytest
from conftest import synthetic_table

pytestmark = pytest.mark.integration


@pytest.fixture
def env(monkeypatch, tmp_path):
    staging = tmp_path / "raw"
    staging.mkdir()
    db_file = tmp_path / "warehouse.duckdb"
    monkeypatch.setenv("DB_CONN", f"duckdb:///{db_file}")
    monkeypatch.setenv("SOURCE_BASE_URL", "https://example.test/trip-data")
    monkeypatch.setenv("SOURCE_FILE_PATTERN", "green_tripdata_{partition}.parquet")
    monkeypatch.setenv("PARTITIONS", "2025-01,2025-02")
    monkeypatch.setenv("STAGING_DIR", str(staging))
    for partition in ("2025-01", "2025-02"):
        pq.write_table(
            synthetic_table(), staging / f"green_tripdata_{partition}.parquet"
        )
    return staging


def counts():
    from data_pipeline.db import connect

    con = connect(read_only=True)
    try:
        return dict(
            con.execute(
                "select source_partition, count(*) from raw_green_trips group by 1"
            ).fetchall()
        )
    finally:
        con.close()


def test_raw_row_count_matches_source(env):
    """A1: raw rows for a partition equal the rows of its source file."""
    from data_pipeline.ingest.load import load_partition

    loaded = load_partition("2025-01")
    source_rows = pq.read_metadata(env / "green_tripdata_2025-01.parquet").num_rows
    assert loaded == source_rows
    assert counts() == {"2025-01": source_rows}


def test_load_is_idempotent(env):
    from data_pipeline.ingest.load import load_partition

    load_partition("2025-01")
    load_partition("2025-02")
    first = counts()
    load_partition("2025-01")  # same partition again
    assert counts() == first
    assert set(first) == {"2025-01", "2025-02"}


def test_schema_drift_fails_and_keeps_old_rows(env):
    from data_pipeline.ingest.load import SchemaDriftError, load_partition

    load_partition("2025-01")
    before = counts()
    drifted = synthetic_table().drop_columns(["total_amount"])
    pq.write_table(drifted, env / "green_tripdata_2025-01.parquet")
    with pytest.raises(SchemaDriftError):
        load_partition("2025-01")
    assert counts() == before


def test_missing_partition_file_fails(env):
    from data_pipeline.ingest.load import LoadError, load_partition

    (env / "green_tripdata_2025-02.parquet").unlink()
    with pytest.raises(LoadError):
        load_partition("2025-02")


def test_load_cli(env):
    from click.testing import CliRunner
    from data_pipeline.ingest.load import main

    runner = CliRunner()
    assert runner.invoke(main, ["2025-01"]).exit_code == 0
    assert runner.invoke(main, ["2025-07"]).exit_code != 0
    assert counts() == {"2025-01": 9}
