# Data Pipeline Project

This repository is used for a ETL data pipeline project. It builds a pipeline that takes raw NYC taxi trip records and turns them into a processed result.

## Objectives

- Writes a script that downloads a public dataset into a local staging directory.
- Builds a pipeline that reads staged Parquet files and aggregates them into daily metrics.
- Separates the pipeline into distinct extract, transform, and load stages.
- Explains the difference between ETL and ELT, and justify which one your pipeline uses.
- Orchestrates a pipeline with Prefect.
- Document scripts, package, and tests.
- Uses pull requests to track the progress.

## Project Brief

This project builds a data pipeline that processes the `Green Taxi Trips` portion of the [NYC Taxi Trip dataset](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

1. Writes a script that downloads the data for the first three months of 2025 and stores it in a local staging directory.
2. Writes an ELT pipeline that reads the locally staged files, processes the data, and calculates revenue per day.
3. Use Prefect for workflow orchestration.

## Tools

| Axis           | Choice                                                    |
| -------------- | --------------------------------------------------------- |
| Database       | `duckdb`                                                  |
| Transform      | `dbt` (with the DuckDB adapter)                           |
| Orchestrator   | `prefect`                                                 |
| Extract, load  | `requests` plus `click`, with DuckDB's own Parquet reader |
| Tests          | `pytest`                                                  |
| Lint and types | `ruff`, plus the template's `ty`                          |

## Additional Folders and Files

| File / Folder                        | Description                             |
| ------------------------------------ | --------------------------------------- |
| [**pyproject.toml**](pyproject.toml) | Project configuration and dependencies. |
| [**uv.lock**](uv.lock)               | Dependency lock file.                   |

## Setup

Use [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.13.5 or newer
and Python 3.13.17 or a newer 3.13 patch release, as defined in
[`.python-version`](.python-version).

> [!NOTE]
> Throughout these steps, text in angle brackets like `<repo-name>` is a **placeholder**. Replace it, including the `< >` brackets, with your own value. For example, `cd <repo-name>` becomes `cd mle-data-pipeline-project`.
