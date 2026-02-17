"""Process YCloud status webhooks and update message delivery state."""
from __future__ import annotations

import logging
from typing import Any, Dict

import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

_STATUS_TO_COLUMN = {
    "accepted": None,
    "sent": "sent_at",
    "delivered": "delivered_at",
    "read": "read_at",
    "failed": None,
}


def _extract_status_payload(payload: Dict[str, Any]) -> tuple[str | None, str | None, Dict[str, Any]]:
    message_id = payload.get("message_id") or payload.get("id")
    status = payload.get("status")

    if not message_id or not status:
        entry = payload.get("entry", [])
        if entry:
            changes = entry[0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
                statuses = value.get("statuses", [])
                if statuses:
                    status_item = statuses[0]
                    message_id = status_item.get("id") or message_id
                    status = status_item.get("status") or status

    status_norm = (status or "").lower().strip()
    return message_id, status_norm, payload


def main(payload: Dict[str, Any], pg_resource: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "invalid_payload"}
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    message_id, status, raw_payload = _extract_status_payload(payload)
    if not message_id or not status:
        return {"ok": False, "error": "missing_fields"}
    if status not in _STATUS_TO_COLUMN:
        return {"ok": False, "error": "unsupported_status", "status": status}

    conn = None
    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor() as cur:
            if _STATUS_TO_COLUMN[status]:
                column = _STATUS_TO_COLUMN[status]
                cur.execute(
                    f"""
                    UPDATE ek_ycloud_messages
                    SET status = %s,
                        {column} = NOW()
                    WHERE ycloud_message_id = %s
                    """,
                    (status, message_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE ek_ycloud_messages
                    SET status = %s
                    WHERE ycloud_message_id = %s
                    """,
                    (status, message_id),
                )

            if cur.rowcount == 0:
                return {"ok": False, "error": "message_not_found", "message_id": message_id}

            cur.execute(
                """
                INSERT INTO ek_lead_events (lead_id, event_type, payload)
                SELECT lead_id, 'ycloud_message_status', %s::jsonb
                FROM ek_ycloud_messages
                WHERE ycloud_message_id = %s
                LIMIT 1
                """,
                (Json({"message_id": message_id, "status": status, "raw": raw_payload}), message_id),
            )

        conn.commit()
        return {"ok": True, "message_id": message_id, "status": status}
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("ycloud_webhook_status failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
