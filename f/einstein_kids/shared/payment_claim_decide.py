"""Confirm or reject an existing payment claim."""
from __future__ import annotations

import logging
from typing import Any, Dict

import psycopg2
from psycopg2.extras import Json, RealDictCursor

logger = logging.getLogger(__name__)


def main(
    sale_id: str,
    action: str,
    actor: str,
    reason: str | None = None,
    pg_resource: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    action_norm = (action or "").upper().strip()
    if action_norm not in ("CONFIRM", "REJECT"):
        return {"ok": False, "error": "invalid_action"}
    if not sale_id:
        return {"ok": False, "error": "missing_sale_id"}
    if not actor:
        return {"ok": False, "error": "missing_actor"}
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    conn = None
    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT sale_id, lead_id, status FROM ek_sales WHERE sale_id = %s FOR UPDATE",
                (sale_id,),
            )
            sale = cur.fetchone()
            if not sale:
                return {"ok": False, "error": "sale_not_found"}

            new_status = "confirmed" if action_norm == "CONFIRM" else "rejected"
            cur.execute(
                """
                UPDATE ek_sales
                SET status = %s,
                    confirmed_by = %s,
                    confirmed_at = NOW(),
                    updated_at = NOW(),
                    proof = COALESCE(proof, '{}'::jsonb) || %s::jsonb
                WHERE sale_id = %s
                """,
                (
                    new_status,
                    actor,
                    Json({"decision_reason": reason} if reason else {}),
                    sale_id,
                ),
            )

            if new_status == "confirmed":
                cur.execute(
                    """
                    UPDATE ek_leads
                    SET stage = 'CUSTOMER', score = score + 100, updated_at = NOW()
                    WHERE lead_id = %s
                    """,
                    (sale["lead_id"],),
                )
                cur.execute(
                    """
                    UPDATE ek_jobs
                    SET status = 'cancelled', updated_at = NOW()
                    WHERE lead_id = %s AND status = 'scheduled'
                    """,
                    (sale["lead_id"],),
                )
            else:
                cur.execute(
                    """
                    UPDATE ek_leads
                    SET score = GREATEST(score - 20, 0), updated_at = NOW()
                    WHERE lead_id = %s
                    """,
                    (sale["lead_id"],),
                )

            cur.execute(
                """
                INSERT INTO ek_lead_events (lead_id, event_type, payload)
                VALUES (%s, 'payment_claim_decided', %s::jsonb)
                """,
                (
                    sale["lead_id"],
                    Json(
                        {
                            "sale_id": sale_id,
                            "decision": action_norm,
                            "status": new_status,
                            "actor": actor,
                            "reason": reason,
                        }
                    ),
                ),
            )

        conn.commit()
        return {
            "ok": True,
            "sale_id": sale_id,
            "decision": action_norm,
            "status": new_status,
            "actor": actor,
            "reason": reason,
        }
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("payment_claim_decide failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
