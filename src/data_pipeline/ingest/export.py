import logging
from pathlib import Path

from .. import config
from ..db import connect

log = logging.getLogger(__name__)

OUTPUT_NAME = "daily_revenue.parquet"


def export_mart() -> Path:
    """Write mart_daily_revenue to the processed folder. A rerun overwrites the file."""
    out_dir = Path(config.processed_dir())
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / OUTPUT_NAME
    con = connect(read_only=True)
    try:
        con.execute(
            "copy (select pickup_date, revenue, trip_count from mart_daily_revenue "
            "order by pickup_date) to ? (format parquet)",
            [str(path)],
        )
        (rows,) = con.execute("select count(*) from mart_daily_revenue").fetchone()
    finally:
        con.close()
    log.info("exported %d rows to %s", rows, path)
    return path
