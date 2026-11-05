import pyarrow as pa
import pyarrow.parquet as pq
import pytest

BASE_URL = "https://example.test/trip-data"
PATTERN = "green_tripdata_{partition}.parquet"


@pytest.fixture
def cfg(monkeypatch, tmp_path):
    """Download settings come from the environment only."""
    staging = tmp_path / "raw"
    monkeypatch.setenv("SOURCE_BASE_URL", BASE_URL)
    monkeypatch.setenv("SOURCE_FILE_PATTERN", PATTERN)
    monkeypatch.setenv("PARTITIONS", "2025-01,2025-02,2025-03")
    monkeypatch.setenv("STAGING_DIR", str(staging))
    return staging


class FakeFetch:
    """Stands in for the network: records urls and writes a tiny Parquet file."""

    def __init__(self):
        self.urls = []

    def __call__(self, url, dest):
        self.urls.append(url)
        pq.write_table(pa.table({"total_amount": [1.0, 2.0]}), dest)


def test_download_urls_built_from_config(cfg, monkeypatch):
    from data_pipeline.ingest.download import build_url

    assert build_url("2025-02") == f"{BASE_URL}/green_tripdata_2025-02.parquet"
    monkeypatch.setenv("SOURCE_BASE_URL", "https://other.test/files")
    assert build_url("2025-02").startswith("https://other.test/files/")


def test_download_writes_staged_files(cfg):
    from data_pipeline.ingest.download import download_partition

    fetch = FakeFetch()
    path = download_partition("2025-01", fetch=fetch)

    assert path == cfg / "green_tripdata_2025-01.parquet"
    assert path.exists()
    assert fetch.urls == [f"{BASE_URL}/green_tripdata_2025-01.parquet"]


def test_download_skips_existing_unless_forced(cfg):
    from data_pipeline.ingest.download import download_partition

    fetch = FakeFetch()
    download_partition("2025-01", fetch=fetch)
    download_partition("2025-01", fetch=fetch)
    assert len(fetch.urls) == 1

    download_partition("2025-01", fetch=fetch, force=True)
    assert len(fetch.urls) == 2


def test_download_failure_is_loud(cfg):
    from data_pipeline.ingest.download import DownloadError, download_partition

    def failing(url, dest):
        raise ConnectionError("no route")

    with pytest.raises(DownloadError):
        download_partition("2025-01", fetch=failing)
    assert not (cfg / "green_tripdata_2025-01.parquet").exists()


def test_download_unreadable_file_is_loud(cfg):
    from data_pipeline.ingest.download import DownloadError, download_partition

    def garbage(url, dest):
        dest.write_bytes(b"not parquet")

    with pytest.raises(DownloadError):
        download_partition("2025-01", fetch=garbage)
    assert not (cfg / "green_tripdata_2025-01.parquet").exists()


def test_download_unknown_partition_is_loud(cfg):
    from data_pipeline.ingest.download import DownloadError, download_partition

    fetch = FakeFetch()
    with pytest.raises(DownloadError):
        download_partition("2025-07", fetch=fetch)
    assert fetch.urls == []
