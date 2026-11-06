"""Contract tests for the pipeline image. Need Docker; skipped without it. No network is used."""

import importlib.util
import shutil
import subprocess
import uuid
from pathlib import Path

import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]

# Reuse the synthetic partition from the integration tests without clashing with tests/conftest.py.
_spec = importlib.util.spec_from_file_location(
    "integration_fixtures", ROOT / "tests" / "integration" / "conftest.py"
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
PARTITION = _fixtures.PARTITION
synthetic_table = _fixtures.synthetic_table

pytestmark = pytest.mark.docker


def _docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    return (
        subprocess.run(["docker", "info"], capture_output=True, check=False).returncode
        == 0
    )


if not _docker_ready():
    pytest.skip("Docker is not available", allow_module_level=True)


@pytest.fixture(scope="module")
def project():
    """A throwaway compose project name, so tests never touch the real data volume."""
    name = f"pipetest{uuid.uuid4().hex[:8]}"
    yield name
    subprocess.run(
        ["docker", "compose", "-p", name, "down", "-v", "--remove-orphans"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )


def compose(project: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-p", project, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_image_builds(project):
    result = compose(project, "build")
    assert result.returncode == 0, result.stderr


def test_pipeline_container_runs_fixture_partition(project, tmp_path):
    seed = tmp_path / "seed"
    seed.mkdir()
    pq.write_table(synthetic_table(), seed / f"green_tripdata_{PARTITION}.parquet")
    # Seed the staging folder in the data volume, so the download step finds the file.
    put = compose(
        project,
        "run",
        "--rm",
        "-v",
        f"{seed}:/seed:ro",
        "--entrypoint",
        "sh",
        "pipeline",
        "-c",
        "mkdir -p data/raw && cp /seed/*.parquet data/raw/",
    )
    assert put.returncode == 0, put.stderr
    run = compose(project, "run", "--rm", "pipeline", PARTITION)
    assert run.returncode == 0, run.stdout + run.stderr
    listing = compose(
        project, "run", "--rm", "--entrypoint", "ls", "pipeline", "data/processed"
    )
    assert "daily_revenue.parquet" in listing.stdout, listing.stderr


def test_image_has_no_env_file(project):
    result = compose(
        project,
        "run",
        "--rm",
        "--entrypoint",
        "sh",
        "pipeline",
        "-c",
        "ls -A /app | grep -x -e '.env' -e '.env.*' && exit 1; exit 0",
    )
    assert result.returncode == 0, result.stdout
