from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from .core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Default to SQLite in dev if no DATABASE_URL set, Postgres in Docker compose
DATABASE_URL = settings.database_url or "sqlite:///./mra.db"

engine = create_engine(str(DATABASE_URL), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a DB session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
