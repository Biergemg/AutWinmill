from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _db_url() -> str:
    configured = os.getenv("OPERATOR_DB_URL")
    if configured:
        return configured
    default_data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir = Path(os.getenv("OPERATOR_DATA_DIR", str(default_data_dir)))
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'console.db'}"


DATABASE_URL = _db_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def _column_exists(inspector: Inspector, table_name: str, column_name: str) -> bool:
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def bootstrap_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    statements: list[str] = []
    if inspector.has_table("clients") and not _column_exists(inspector, "clients", "tenant_id"):
        statements.append("ALTER TABLE clients ADD COLUMN tenant_id VARCHAR(80) NOT NULL DEFAULT 'default'")
    if inspector.has_table("automations") and not _column_exists(inspector, "automations", "tenant_id"):
        statements.append("ALTER TABLE automations ADD COLUMN tenant_id VARCHAR(80) NOT NULL DEFAULT 'default'")
    if inspector.has_table("executions") and not _column_exists(inspector, "executions", "tenant_id"):
        statements.append("ALTER TABLE executions ADD COLUMN tenant_id VARCHAR(80) NOT NULL DEFAULT 'default'")
    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
    with engine.begin() as conn:
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_clients_tenant_name ON clients (tenant_id, name)"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
