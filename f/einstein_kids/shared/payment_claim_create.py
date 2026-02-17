"""Create or upsert a payment claim for a lead."""
from __future__ import annotations

import logging
from typing import Any, Dict

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _normalize_amount(proof: Dict[str, Any] | None) -> float | None:
    if not proof:
        return None
    raw = proof.get("amount")
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def main(
    lead_id: str,
    proof: Dict[str, Any] | None = None,
    pg_resource: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if not lead_id:
        return {"ok": False, "error": "missing_lead_id"}
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    conn = None
    try:
        amount = _normalize_amount(proof)
        currency = (proof or {}).get("currency", "MXN")
        external_ref = (proof or {}).get("external_ref")

        conn = psycopg2.connect(**pg_resource)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM ek_leads WHERE lead_id = %s", (lead_id,))
            if not cur.fetchone():
                return {"ok": False, "error": "lead_not_found"}

            cur.execute(
                """
                INSERT INTO ek_sales (lead_id, provider, status, amount, currency, external_ref, proof)
                VALUES (%s, 'vitalhealth', 'claimed', %s, %s, %s, %s::jsonb)
                RETURNING sale_id, status, created_at
                """,
                (lead_id, amount, currency, external_ref, psycopg2.extras.Json(proof or {})),
            )
            sale = cur.fetchone()

            cur.execute(
                """
                INSERT INTO ek_lead_events (lead_id, event_type, payload)
                VALUES (%s, 'payment_claim_created', %s::jsonb)
                """,
                (
                    lead_id,
                    psycopg2.extras.Json(
                        {
                            "sale_id": str(sale["sale_id"]),
                            "amount": amount,
                            "currency": currency,
                            "external_ref": external_ref,
                        }
                    ),
                ),
            )

            cur.execute(
                "UPDATE ek_leads SET score = score + 30, updated_at = NOW() WHERE lead_id = %s",
                (lead_id,),
            )

        conn.commit()
        return {
            "ok": True,
            "lead_id": lead_id,
            "sale_id": str(sale["sale_id"]),
            "status": sale["status"],
        }
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("payment_claim_create failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
