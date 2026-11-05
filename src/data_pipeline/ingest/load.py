import logging

import click

from .. import config
from ..db import connect
from .download import staged_path

log = logging.getLogger(__name__)

# Source columns and types the loader expects (TLC green trips, checked on the 2025-01 file).
# Staging selects every column except ehail_fee, so each of those must keep its type.
EXPECTED_TYPES = {
    "VendorID": "INTEGER",
    "lpep_pickup_datetime": "TIMESTAMP",
    "lpep_dropoff_datetime": "TIMESTAMP",
    "store_and_fwd_flag": "VARCHAR",
    "RatecodeID": "BIGINT",
    "PULocationID": "INTEGER",
    "DOLocationID": "INTEGER",
    "passenger_count": "BIGINT",
    "trip_distance": "DOUBLE",
    "fare_amount": "DOUBLE",
    "extra": "DOUBLE",
    "mta_tax": "DOUBLE",
    "tip_amount": "DOUBLE",
    "tolls_amount": "DOUBLE",
    "improvement_surcharge": "DOUBLE",
    "total_amount": "DOUBLE",
    "payment_type": "BIGINT",
    "trip_type": "BIGINT",
    "congestion_surcharge": "DOUBLE",
    "cbd_congestion_fee": "DOUBLE",
}
# Kept in raw, dropped in staging (always null in January): the name must exist, the type is not checked.
NAME_ONLY_COLUMNS = {"ehail_fee"}
EXPECTED_COLUMNS = set(EXPECTED_TYPES) | NAME_ONLY_COLUMNS


class LoadError(Exception):
    pass


class SchemaDriftError(LoadError):
    pass


def check_schema(con, path) -> None:
    described = con.execute(
        "describe select * from read_parquet(?)", [str(path)]
    ).fetchall()
    found = {name: dtype for name, dtype, *_ in described}
    missing = EXPECTED_COLUMNS - set(found)
    extra = set(found) - EXPECTED_COLUMNS
    if missing or extra:
        raise SchemaDriftError(
            f"schema changed: missing {sorted(missing)}, extra {sorted(extra)}"
        )
    changed = {
        name: f"{found[name]} (expected {expected})"
        for name, expected in EXPECTED_TYPES.items()
        if found[name] != expected
    }
    if changed:
        raise SchemaDriftError(f"column types changed: {changed}")


def load_partition(partition: str) -> int:
    """Replace one partition in raw_green_trips, in one transaction. Returns the rows loaded."""
    path = staged_path(partition)
    if not path.exists():
        raise LoadError(f"no staged file for {partition}: {path}")
    con = connect()
    try:
        check_schema(con, path)
        (rows_in,) = con.execute(
            "select count(*) from read_parquet(?)", [str(path)]
        ).fetchone()
        con.execute("begin")
        try:
            con.execute(
                "create table if not exists raw_green_trips as "
                "select *, current_timestamp::timestamp as loaded_at, "
                "''::varchar as source_partition from read_parquet(?) limit 0",
                [str(path)],
            )
            (deleted,) = con.execute(
                "select count(*) from raw_green_trips where source_partition = ?",
                [partition],
            ).fetchone()
            con.execute(
                "delete from raw_green_trips where source_partition = ?", [partition]
            )
            con.execute(
                "insert into raw_green_trips by name "
                "select *, current_timestamp::timestamp as loaded_at, ? as source_partition "
                "from read_parquet(?)",
                [partition, str(path)],
            )
            (rows_out,) = con.execute(
                "select count(*) from raw_green_trips where source_partition = ?",
                [partition],
            ).fetchone()
            if rows_out != rows_in:
                raise LoadError(f"{partition}: read {rows_in} rows, loaded {rows_out}")
            con.execute("commit")
        except BaseException:
            con.execute("rollback")
            raise
        log.info(
            "loaded %s: %d rows in, %d out, %d replaced",
            partition,
            rows_in,
            rows_out,
            deleted,
        )
        return rows_out
    finally:
        con.close()


@click.command()
@click.argument("partition")
def main(partition: str) -> None:
    logging.basicConfig(level=logging.INFO)
    if partition not in config.partitions():
        raise click.ClickException(f"partition {partition} is not in PARTITIONS")
    try:
        rows = load_partition(partition)
    except LoadError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"{partition}: {rows} rows")


if __name__ == "__main__":
    main()
