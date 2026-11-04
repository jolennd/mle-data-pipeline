import os

import pytest


@pytest.fixture(scope="session")
def engine():
    """Test database engine. Needs sqlalchemy, so imports stay inside the fixture."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    url = os.environ.get("TEST_DB_CONN", "sqlite+pysqlite:///:memory:")
    kwargs = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, **kwargs)
