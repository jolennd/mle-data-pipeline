from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "data_pipeline"


def test_database_is_opened_only_in_db_py():
    """Every connection goes through db.connect(), which reads DB_CONN from the environment."""
    offenders = []
    for path in SRC.rglob("*.py"):
        if path.name == "db.py":
            continue
        text = path.read_text()
        if "duckdb.connect" in text or ".duckdb" in text or "DB_CONN" in text:
            offenders.append(str(path.relative_to(SRC)))
    assert offenders == []
