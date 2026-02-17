"""Cancel scheduled jobs for a lead."""
from __future__ import annotations

import logging
from typing import Any, Dict

import psycopg2

logger = logging.getLogger(__name__)


def main(lead_id: str, pg_resource: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not lead_id:
        return {"ok": False, "error": "missing_lead_id"}
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    conn = None
    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ek_jobs
                SET status = 'cancelled', updated_at = NOW()
                WHERE lead_id = %s AND status = 'scheduled'
                """,
                (lead_id,),
            )
            cancelled = cur.rowcount
        conn.commit()
        return {"ok": True, "lead_id": lead_id, "cancelled": cancelled}
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("cancel_jobs failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
