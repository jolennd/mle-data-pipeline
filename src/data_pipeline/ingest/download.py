import logging
from pathlib import Path

import click
import pyarrow.parquet as pq
import requests

from .. import config

log = logging.getLogger(__name__)


class DownloadError(Exception):
    pass


def build_url(partition: str) -> str:
    name = config.source_file_pattern().format(partition=partition)
    return f"{config.source_base_url()}/{name}"


def staged_path(partition: str) -> Path:
    name = config.source_file_pattern().format(partition=partition)
    return Path(config.staging_dir()) / name


def http_fetch(url: str, dest: Path) -> None:
    """The only function that touches the network."""
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(dest, "wb") as out:
            out.writelines(response.iter_content(chunk_size=1 << 20))


def download_partition(partition: str, *, fetch=None, force: bool = False) -> Path:
    fetch = fetch or http_fetch
    if partition not in config.partitions():
        raise DownloadError(f"partition {partition} is not in PARTITIONS")
    path = staged_path(partition)
    if path.exists() and not force:
        log.info("skip existing file %s", path)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    try:
        fetch(build_url(partition), tmp)
        pq.ParquetFile(tmp)  # raises when the file is not readable Parquet
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise DownloadError(f"download of {partition} failed: {exc}") from exc
    tmp.replace(path)
    log.info("downloaded %s to %s", partition, path)
    return path


@click.command()
@click.argument("partition")
@click.option("--force", is_flag=True, help="Download again even if the file exists.")
def main(partition: str, force: bool) -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        path = download_partition(partition, force=force)
    except DownloadError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(path)


if __name__ == "__main__":
    main()
