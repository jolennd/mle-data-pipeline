| Source | Location | Refresh | Owner | Notes |
|---|---|---|---|---|
| NYC Green Taxi trip records, Parquet, one file per month (2025-01, 2025-02, 2025-03) | NYC Taxi and Limousine Commission (TLC) public trip data. Base URL and file name pattern live in config, not in code. To confirm in phase 2: pattern `green_tripdata_YYYY-MM.parquet` | Published monthly by the source. This project is a fixed backfill of Jan to Mar 2025, no live refresh | NYC TLC | Columns the output needs: `lpep_pickup_datetime` (sets the day) and `total_amount` (revenue, negatives kept). Files can contain rows with pickup dates outside their own month (ADR 2). Local copy is saved to the git-ignored `data/raw/` staging folder. |

## Exploration findings
Not written yet. The phase 2 exploration notebook reads one staged file and records here: column types, missing values, value ranges for `lpep_pickup_datetime` and `total_amount`, the real row count per month (the expected values for A1), and what needs cleaning. Each finding becomes a data test or an ADR.
