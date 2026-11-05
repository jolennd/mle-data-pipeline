"""Small query helpers shared by the integration tests."""


def columns_of(con, table):
    rows = con.execute(
        "select column_name from information_schema.columns where table_name = ?",
        [table],
    ).fetchall()
    return {r[0] for r in rows}


def schema_of(con, table):
    """Tables may sit in different schemas; find the one table by name."""
    rows = con.execute(
        "select table_schema from information_schema.tables where table_name = ?",
        [table],
    ).fetchall()
    assert len(rows) == 1, f"{table} must exist exactly once, found {rows}"
    return f"{rows[0][0]}.{table}"
