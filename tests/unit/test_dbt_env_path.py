import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "url",
    [
        "duckdb:///data/warehouse.duckdb",
        "duckdb:////var/tmp/warehouse.duckdb",
    ],
)
def test_duckdb_path_matches_dbt_env(url, tmp_path):
    """db.duckdb_path() and transform/dbt_env.py must open the same file for one DB_CONN."""
    from data_pipeline.db import duckdb_path

    fake_dbt = tmp_path / "dbt"
    fake_dbt.write_text('#!/bin/sh\necho "$DBT_DUCKDB_PATH"\n')
    fake_dbt.chmod(0o755)
    env = {**os.environ, "DB_CONN": url, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    result = subprocess.run(
        [sys.executable, str(ROOT / "transform" / "dbt_env.py"), "run"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == duckdb_path(url)
