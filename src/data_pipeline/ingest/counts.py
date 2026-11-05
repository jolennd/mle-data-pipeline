import logging

from ..db import connect

log = logging.getLogger(__name__)


def layer_counts(con, partition: str) -> dict:
    (raw,) = con.execute(
        "select count(*) from raw_green_trips where source_partition = ?", [partition]
    ).fetchone()
    (null_pickup,) = con.execute(
        "select count(*) from raw_green_trips "
        "where source_partition = ? and lpep_pickup_datetime is null",
        [partition],
    ).fetchone()
    (staged,) = con.execute(
        "select count(*) from stg_green_trips where source_partition = ?", [partition]
    ).fetchone()
    (mart_days,) = con.execute("select count(*) from mart_daily_revenue").fetchone()
    return {
        "raw": raw,
        "staged": staged,
        "excluded_null_pickup": null_pickup,
        "excluded_out_of_range": raw - staged - null_pickup,
        "mart_days": mart_days,
    }


def log_layer_counts(partition: str) -> dict:
    """Log raw, staged, excluded and mart counts for a partition, and return them."""
    con = connect(read_only=True)
    try:
        counts = layer_counts(con, partition)
    finally:
        con.close()
    log.info(
        "%s: raw %d, staged %d, excluded %d (no pickup time %d, outside range %d), mart days %d",
        partition,
        counts["raw"],
        counts["staged"],
        counts["excluded_null_pickup"] + counts["excluded_out_of_range"],
        counts["excluded_null_pickup"],
        counts["excluded_out_of_range"],
        counts["mart_days"],
    )
    return counts
