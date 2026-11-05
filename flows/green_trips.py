"""Orchestrated run of the green trips pipeline.

Each task is a thin wrapper around the function the plain entry point
(data_pipeline.pipeline) calls, in the same order. No data logic lives here.
Functions are looked up on the pipeline module at call time.
"""

import re

from prefect import flow, get_run_logger, task

from data_pipeline import config, pipeline

PARTITION_FORMAT = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def check_partition(partition: str) -> None:
    """One month, written YYYY-MM, and one of the configured PARTITIONS."""
    if not PARTITION_FORMAT.match(partition or ""):
        raise ValueError(f"partition {partition!r} is not a month written YYYY-MM")
    if partition not in config.partitions():
        raise ValueError(f"partition {partition} is not in PARTITIONS")


# Only the download touches the network, so only it retries (M5 idempotent steps).
@task(retries=3, retry_delay_seconds=60)
def download(partition: str) -> None:
    pipeline.download_partition(partition)


@task
def load(partition: str) -> None:
    pipeline.load_partition(partition)


@task
def transform(partition: str) -> None:
    pipeline.run_transform()
    pipeline.log_layer_counts(partition)


@task
def export() -> None:
    pipeline.export_mart()


@flow(flow_run_name="green-trips-{partition}")
def green_trips_flow(partition: str) -> None:
    check_partition(partition)
    get_run_logger().info("partition %s", partition)
    download(partition)
    load(partition)
    transform(partition)
    export()


@flow(flow_run_name="green-trips-all")
def green_trips_all(partitions: list[str] | None = None) -> None:
    """Months one after another. DuckDB has one writer, and the boundary days
    are complete only after every month is loaded."""
    for partition in partitions or config.partitions():
        green_trips_flow(partition)
