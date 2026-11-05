# Data Pipeline Project

This repository is used for an ELT data pipeline project. It builds a pipeline that takes raw NYC taxi trip records and turns them into a processed result.

## Objectives

- Writes a script that downloads a public dataset into a local staging directory.
- Builds a pipeline that reads staged Parquet files and aggregates them into daily metrics.
- Separates the pipeline into distinct extract, transform, and load stages.
- Explains the difference between ETL and ELT, and justifies which one the pipeline uses.
- Orchestrates a pipeline with Prefect.
- Documents scripts, package, and tests.
- Uses pull requests to track the progress.

## Project Brief

This project builds a data pipeline that processes the `Green Taxi Trips` portion of the [NYC Taxi Trip dataset](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

1. Writes a script that downloads the data for the first three months of 2025 and stores it in a local staging directory.
2. Writes an ELT pipeline that reads the locally staged files, processes the data, and calculates revenue per day.
3. Uses Prefect for workflow orchestration.

## Tools

| Axis           | Choice                                                    |
| -------------- | --------------------------------------------------------- |
| Database       | `duckdb`                                                  |
| Transform      | `dbt` (with the DuckDB adapter)                           |
| Orchestrator   | `prefect`                                                 |
| Extract, load  | `requests` plus `click`, with DuckDB's own Parquet reader |
| Tests          | `pytest`                                                  |
| Lint and types | `ruff`, plus the template's `ty`                          |

## Project Structure

```
mle-data-pipeline/
├── data/
│   ├── raw/              # Step 1: staged Parquet downloads, never edited (git-ignored)
│   └── processed/        # Step 3: daily revenue output exported from the mart
├── notebooks/            # Step 2: data exploration only, not part of the pipeline
├── src/
│   └── data_pipeline/    # Steps 1 and 3: download, load, export, plain entry point
├── transform/            # Step 3: dbt project (staging and mart models)
├── flows/                # Step 4: Prefect flow and its entry point
├── tests/                # Unit and integration tests
├── docs/                 # Brief, traceability, data sources, design, ADRs
├── Makefile              # Run, test, and orchestration targets
├── pyproject.toml        # Project configuration and dependencies
└── uv.lock               # Dependency lock file
```

| File / Folder                             | Description                                                          |
| ----------------------------------------- | -------------------------------------------------------------------- |
| `data/raw/`                               | Monthly Green Taxi Parquet files for Jan to Mar 2025, as downloaded. |
| `data/processed/`                         | Daily revenue result written by the pipeline.                        |
| `notebooks/`                              | Exploration of columns, types, missing values, and value ranges.     |
| [`src/data_pipeline/`](src/data_pipeline) | Python package: download, load into DuckDB, export, entry point.     |
| [`transform/`](transform)                 | dbt project with `stg_green_trips` and `mart_daily_revenue`.         |
| [`flows/`](flows)                         | Prefect flow with download, load, and transform tasks.               |
| [`tests/`](tests)                         | Tests for download, load, transform, reconciliation, and the flow.   |
| [`docs/`](docs)                           | Project brief, traceability table, design notes, and ADRs.           |
| [**pyproject.toml**](pyproject.toml)      | Project configuration and dependencies.                              |
| [**uv.lock**](uv.lock)                    | Dependency lock file.                                                |

### Additional Info

- The Prefect flow lives in `flows/` at the repository root instead of inside `src/data_pipeline/`. This keeps orchestration separate from the pipeline logic, which runs on its own without Prefect.
- The SQL transforms live in a dbt project in `transform/`. dbt needs its own project folder, so the transform stage is not a Python module in `src/`.

## Data Flow

```
NYC TLC Parquet files
  -> data/raw/                (download script)
  -> raw_green_trips          (load into DuckDB, all rows kept)
  -> stg_green_trips          (dbt: typed, cleaned, pickup dates Jan to Mar 2025)
  -> mart_daily_revenue       (dbt: one row per pickup date, sum of total_amount)
  -> data/processed/          (export)
```

## Setup

Use [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.13.5 or newer
and Python 3.13.17 or a newer 3.13 patch release, as defined in
[`.python-version`](.python-version).

> [!NOTE]
> Throughout these steps, text in angle brackets like `<repo-name>` is a **placeholder**. Replace it, including the `< >` brackets, with your own value. For example, `cd <repo-name>` becomes `cd mle-data-pipeline-project`.

## How to Run

To be completed in the final pull request. This section will list the commands to:

1. Install dependencies with `uv sync`.
2. Download the data into `data/raw/`.
3. Run the plain pipeline end to end.
4. Run the pipeline as a Prefect flow.
5. Run the tests.

## Project Review Questions

To be completed in the final pull request.
