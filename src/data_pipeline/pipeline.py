"""Plain entry point: download, load, transform, export for one partition, in order.
The first failing step raises and the steps after it do not run. No orchestrator needed.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import click

from .ingest.counts import log_layer_counts
from .ingest.download import DownloadError, download_partition
from .ingest.export import export_mart
from .ingest.load import load_partition

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]


class TransformError(Exception):
    pass


def run_transform() -> None:
    """Build the models, then run their data tests. Both go through transform/dbt_env.py."""
    script = ROOT / "transform" / "dbt_env.py"
    env = {
        **os.environ,
        "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    for command in ("run", "test"):
        result = subprocess.run(
            [sys.executable, str(script), command], check=False, env=env, cwd=ROOT
        )
        if result.returncode != 0:
            raise TransformError(
                f"dbt {command} failed with exit code {result.returncode}"
            )


def run_pipeline(partition: str, fetch=None) -> Path:
    log.info("step download: %s", partition)
    download_partition(partition, fetch=fetch)
    log.info("step load: %s", partition)
    load_partition(partition)
    log.info("step transform: %s", partition)
    run_transform()
    log_layer_counts(partition)
    log.info("step export: %s", partition)
    return export_mart()


@click.command()
@click.argument("partition")
def main(partition: str) -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        path = run_pipeline(partition)
    except (DownloadError, TransformError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(path)


if __name__ == "__main__":
    main()
