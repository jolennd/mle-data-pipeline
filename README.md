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

All commands go through `make`, which loads `.env`. Settings are never hard-coded.

1. Install dependencies and create the local settings file:

   ```bash
   uv sync
   cp .env.example .env
   ```

2. Run the plain pipeline (download, load, transform, export) once per month. Run all three months before reading daily totals, because a day is complete only after every month is loaded:

   ```bash
   make pipeline-run PARTITION=2025-01
   make pipeline-run PARTITION=2025-02
   make pipeline-run PARTITION=2025-03
   ```

3. Or run it as a Prefect flow:

   ```bash
   make flow-run PARTITION=2025-01   # one month
   make flow-run PARTITION=all       # January to March, one after another
   make flow-serve                   # serve the monthly schedule (keeps running, Ctrl+C to stop)
   ```

4. Run the tests:

   ```bash
   make test             # Python tests
   make transform-test   # dbt data tests, run after the pipeline has loaded data
   ```

### Output

The result is written to `data/processed/daily_revenue.parquet` with one row per pickup date (`pickup_date`, `revenue`, `trip_count`). After January to March are loaded, I expect:

| Check         | Expected value |
| ------------- | -------------- |
| Days          | 90             |
| Trips         | 146,475        |
| Total revenue | 3,395,290.56   |

## Project Review Questions

### 1. What are the steps you took to complete the project?

I started with a brief that fixed the grain (one row per pickup date) and the acceptance numbers: raw row counts must equal the source files, and the staged, mart and exported totals must agree within 0.01. I chose revenue as `total_amount` summed as it is (ADR 1) and chose ELT, so the raw data stays untouched and the transforms are versioned SQL.

Then I explored the three monthly files in a notebook and wrote down what I found in `docs/02-data-sources.md`: column types, missing values, negative amounts, and pickup dates outside a file's month. Those findings led to the staging rules in ADR 2 and ADR 15.

I wrote the tests first and committed them failing, then built the pieces in small batches: a download script, a load into `raw_green_trips`, dbt models for staging and the daily mart, an export to Parquet, and a plain entry point that runs the steps in order. Last I wrapped the same functions in Prefect flows with retries on the download and a monthly schedule (ADR 17). Each stage was reviewed against its gate before I merged it.

### 2. What challenges did you face?

- **Neighbouring months.** The monthly files contain trips from neighbouring months, for example January 31 trips in the February file. The day comes from the pickup date, not the file, so a day is complete only after all months are loaded. I load one month at a time, and I read daily totals only after all three have run (ADR 2). Eleven rows fall outside January to March and are excluded in staging, counted and logged.
- **Negative reversals.** Between 153 and 165 rows per month have a negative `total_amount`. Most have a positive twin, but not all of them do. Filtering them would overstate revenue, so I sum them as they are and document it (ADR 1).
- **No natural key.** The data has no id column, so I could not deduplicate on a key. I checked that no month has exact duplicate rows, and I decided to stop and report if one ever does instead of dropping rows silently (ADR 13, ADR 15).
- **The package was not installed.** The tests passed because pytest adds `src/` to the import path, but `make download` failed with `No module named 'data_pipeline'`. `pyproject.toml` had no build system, so `uv sync` never installed the package. Adding hatchling as the build backend fixed the commands and let the Prefect flows import the package too.
- **One writer in DuckDB.** The file database allows one writer at a time, so months run one after another, also in the Prefect parent flow.

### 3. What would you do differently if you had more time?

- Build the star schema from ADR 13: a `fct_trips` fact table with `dim_date`, `dim_payment_type`, `dim_vendor` and `dim_ratecode`, and build the daily mart from it. I accepted the design but deferred it, so the mart is currently built straight from staging. The three-way totals check would then also catch a join that drops or doubles trips.
- Add a zone dimension from the TLC zone lookup file, so revenue can be split by pickup and dropoff area. The location ids are already in the data.
- Add data quality alerts, so a failed reconciliation or an unusual count of excluded rows reaches me without my reading the logs.
