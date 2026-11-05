import pytest


def test_connect_reads_db_conn(monkeypatch, tmp_path):
    from data_pipeline.db import connect

    db_file = tmp_path / "warehouse.duckdb"
    monkeypatch.setenv("DB_CONN", f"duckdb:///{db_file}")  # absolute path
    con = connect()
    con.execute("create table t as select 1 as x")
    con.close()
    assert db_file.exists()

    reader = connect(read_only=True)
    assert reader.execute("select x from t").fetchall() == [(1,)]
    reader.close()


def test_connect_relative_path_is_relative_to_working_directory(monkeypatch, tmp_path):
    from data_pipeline.db import connect

    (tmp_path / "data").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_CONN", "duckdb:///data/warehouse.duckdb")
    connect().close()
    assert (tmp_path / "data" / "warehouse.duckdb").exists()


@pytest.mark.parametrize("value", [None, "postgresql://u:p@localhost/db"])
def test_connect_fails_loudly(monkeypatch, value):
    from data_pipeline.db import connect

    if value is None:
        monkeypatch.delenv("DB_CONN", raising=False)
    else:
        monkeypatch.setenv("DB_CONN", value)
    with pytest.raises(ValueError):
        connect()
