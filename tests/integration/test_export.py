import pyarrow.parquet as pq
import pytest
from contract_helpers import schema_of

pytestmark = pytest.mark.integration


def test_export_writes_processed_file(built_db, expected):
    from data_pipeline.ingest.export import export_mart

    path = export_mart()
    assert path.name == "daily_revenue.parquet"
    table = pq.read_table(path)
    assert table.column_names == ["pickup_date", "revenue", "trip_count"]
    assert table.num_rows == expected["mart_days"]
    mart = schema_of(built_db, "mart_daily_revenue")
    (total,) = built_db.execute(f"select sum(revenue) from {mart}").fetchone()
    assert abs(float(sum(v.as_py() for v in table["revenue"])) - float(total)) <= 0.01


def test_export_rerun_overwrites_with_same_content(built_db):
    from data_pipeline.ingest.export import export_mart

    first = pq.read_table(export_mart())
    second = pq.read_table(export_mart())
    assert first.equals(second)
    assert first["pickup_date"].to_pylist() == sorted(first["pickup_date"].to_pylist())
