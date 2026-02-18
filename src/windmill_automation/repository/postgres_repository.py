from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import psycopg2


@dataclass
class PostgresRepository:
    dsn: str | None = None

    def __post_init__(self) -> None:
        if not self.dsn:
            self.dsn = os.getenv("DATABASE_URL")
        if not self.dsn:
            raise RuntimeError("DATABASE_URL is required for PostgresRepository")

    def _connect(self):
        return psycopg2.connect(self.dsn)

    def insert_event(self, event: dict[str, Any]) -> bool:
        sql = """
        INSERT INTO events(event_id, trace_id, payload, status)
        VALUES (%s, %s, %s, %s)
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    event["event_id"],
                    event.get("trace_id"),
                    str(event.get("payload")),
                    event.get("status"),
                ),
            )
        return True

    def update_status(self, event_id: str, status: str) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE events SET status = %s WHERE event_id = %s", (status, event_id))
        return True
