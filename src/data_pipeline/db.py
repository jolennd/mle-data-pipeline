from urllib.parse import urlparse

import duckdb

from .config import require_env


def duckdb_path(url: str) -> str:
    """Same rule as transform/dbt_env.py: duckdb:///rel.duckdb is relative, duckdb:////abs.duckdb is absolute."""
    parsed = urlparse(url)
    if parsed.scheme != "duckdb":
        raise ValueError(f"unsupported DB_CONN scheme: {parsed.scheme!r}")
    path = parsed.path[1:] if parsed.path.startswith("//") else parsed.path.lstrip("/")
    if not path:
        raise ValueError("DB_CONN has no database path")
    return path


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(duckdb_path(require_env("DB_CONN")), read_only=read_only)
