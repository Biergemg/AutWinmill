from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from ..ports.persistence import AuditRecord, PersistencePort

logger = logging.getLogger(__name__)


class DockerPostgresAdapter(PersistencePort):
    """Compatibility adapter kept for legacy call sites.

    Despite the historical name, this version uses direct DB connections with
    parameterized SQL to avoid shell injection risks.
    """

    def __init__(
        self,
        container_name: str = "aut_windmill_postgres",
        db_user: str | None = None,
        db_name: str | None = None,
        db_password: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        dsn: str | None = None,
    ):
        self.container_name = container_name  # kept for backward compatibility
        self.db_user = db_user or os.getenv("POSTGRES_USER", "windmill")
        self.db_name = db_name or os.getenv("POSTGRES_DB", "windmill")
        self.db_password = db_password or os.getenv("POSTGRES_PASSWORD", "")
        self.db_host = db_host or os.getenv("PGHOST", "localhost")
        self.db_port = db_port or int(os.getenv("PGPORT", "5432"))
        self.dsn = dsn or os.getenv("DATABASE_URL")

    @contextmanager
    def _conn(self) -> Iterator:
        conn = None
        try:
            if self.dsn:
                conn = psycopg2.connect(self.dsn)
            else:
                conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    dbname=self.db_name,
                )
            yield conn
        except Exception as exc:  # noqa: BLE001
            msg = f"Error ejecutando SQL: {exc}"
            logger.error(json.dumps({"message": msg}, ensure_ascii=False))
            raise RuntimeError(msg) from exc
        finally:
            if conn is not None:
                conn.close()

    def record_audit_log(self, record: AuditRecord) -> None:
        sql = """
        INSERT INTO audit_log (actor, action, details, trace_id, workflow_id, event_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    record.actor,
                    record.action,
                    Json(record.details),
                    record.trace_id,
                    record.workflow_id,
                    record.event_id,
                ),
            )
            conn.commit()

    def get_audit_logs(self, limit: int = 10) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        sql = """
        SELECT actor, action, details, trace_id, workflow_id, event_id, ts
        FROM audit_log
        ORDER BY ts DESC
        LIMIT %s
        """
        with self._conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (safe_limit,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
