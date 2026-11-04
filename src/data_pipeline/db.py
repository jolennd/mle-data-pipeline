from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from .config import require_env


class Base(DeclarativeBase):
    pass


def make_engine():
    return create_engine(require_env("DB_CONN"))


def get_db(session_factory):
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
