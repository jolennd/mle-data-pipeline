import re
from pathlib import Path

FLOWS = Path(__file__).resolve().parents[2] / "flows"
DEPLOY_FILES = ["prefect.yaml", "deployment.yaml"]

SECRET_PATTERNS = [
    r"(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*[\"'][^\"']+[\"']",
    r"[a-z+]+://[^/\s:@\"']+:[^/\s@\"']+@",  # user:password@host
    r"(?i)duckdb:///|postgres(ql)?://",  # a literal connection string
]


def _files() -> list[Path]:
    found = list(FLOWS.rglob("*.py")) + [
        p for name in DEPLOY_FILES for p in Path(FLOWS.parent).glob(name)
    ]
    return found


def test_flow_files_exist():
    assert any(p.name == "__main__.py" for p in _files())


def test_no_secret_in_flow_files():
    """R17: flow and deployment files hold no secret and no connection string."""
    offenders = []
    for path in _files():
        text = path.read_text()
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text):
                offenders.append(f"{path.name}: {pattern}")
    assert offenders == []


def test_flows_never_open_the_database_themselves():
    """The connection goes through db.py, which reads DB_CONN from the environment."""
    offenders = [
        p.name
        for p in _files()
        if "DB_CONN" in p.read_text() or "duckdb.connect" in p.read_text()
    ]
    assert offenders == []
