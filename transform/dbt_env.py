"""Bridge: dbt cannot read one URL, so split DB_CONN into DBT_* variables, then run dbt.
Usage: python transform/dbt_env.py <dbt args>   e.g.  run | test | debug
Fails loudly if DB_CONN is unset or its scheme is unknown. Stdlib only.
"""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent


def main() -> int:
    url = os.environ.get("DB_CONN")
    if not url:
        sys.exit("DB_CONN is not set. Copy .env.example to .env and load it.")
    parsed = urlparse(url)
    scheme = parsed.scheme.split("+")[
        0
    ]  # drop the driver part, e.g. postgresql+psycopg
    env = dict(os.environ)
    if scheme in ("postgresql", "postgres"):
        target = "postgres"
        env.update(
            DBT_HOST=parsed.hostname or "",
            DBT_PORT=str(parsed.port or 5432),
            DBT_USER=unquote(parsed.username or ""),
            DBT_PASSWORD=unquote(parsed.password or ""),
            DBT_DBNAME=parsed.path.lstrip("/"),
        )
    elif scheme == "duckdb":
        target = "duckdb"
        env["DBT_DUCKDB_PATH"] = (
            parsed.path[1:] if parsed.path.startswith("//") else parsed.path.lstrip("/")
        )
    else:
        sys.exit(f"unsupported DB_CONN scheme for dbt: {parsed.scheme!r}")
    cmd = [
        "dbt",
        *sys.argv[1:],
        "--profiles-dir",
        str(HERE),
        "--project-dir",
        str(HERE),
        "--target",
        target,
    ]
    return subprocess.call(cmd, env=env)


sys.exit(main())
