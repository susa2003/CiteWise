from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if settings.database_url.startswith("sqlite:"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
    if settings.database_url.startswith("sqlite:"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db():
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
