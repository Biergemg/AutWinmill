from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from windmill_automation.config.settings import get_settings


def _build_engine(database_url: str) -> Engine:
    settings = get_settings()
    return create_engine(
        database_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


_default_engine: Engine | None = None
_default_session_factory = None


def _ensure_default_session_factory():
    global _default_engine
    global _default_session_factory
    if _default_session_factory is not None:
        return _default_session_factory
    settings = get_settings()
    _default_engine = _build_engine(settings.database_url)
    _default_session_factory = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=_default_engine)
    )
    return _default_session_factory


def get_db_session(database_url: str | None = None) -> Generator:
    if database_url:
        temp_engine = _build_engine(database_url)
        temp_session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)
        )
        db = temp_session_factory()
        try:
            yield db
        finally:
            db.close()
            temp_session_factory.remove()
            temp_engine.dispose()
        return

    session_factory = _ensure_default_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def dispose_engine() -> None:
    global _default_engine
    global _default_session_factory
    if _default_session_factory is not None:
        _default_session_factory.remove()
        _default_session_factory = None
    if _default_engine is not None:
        _default_engine.dispose()
        _default_engine = None
