"""Handle inbound YCloud WhatsApp webhooks."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

import psycopg2
from psycopg2.extras import Json

from .normalize_phone import normalize_phone_e164_mx
from .upsert_lead import main as upsert_lead

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InboundResult:
    ok: bool
    lead_id: str | None = None
    action: str | None = None
    error: str | None = None


def _parse_signature_header(sig_header: str) -> tuple[str | None, str | None]:
    parts = {}
    for token in (sig_header or "").split(","):
        token = token.strip()
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parts[key.strip()] = value.strip()
    return parts.get("t"), parts.get("v1")


def verify_signature(secret: str, body: str, signature: str, timestamp: str) -> bool:
    if not secret or not signature or not timestamp:
        return False

    try:
        ts = int(timestamp)
    except ValueError:
        return False

    now = int(time.time())
    if abs(now - ts) > 300:
        logger.warning("Webhook timestamp outside tolerance")
        return False

    payload = f"{timestamp}.{body}"
    computed = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


def _should_require_signature(secret: str | None) -> bool:
    if secret:
        return True
    return os.getenv("ALLOW_INSECURE_WEBHOOK", "false").lower() not in ("1", "true", "yes")


def _extract_message(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        return messages[0] if messages else None
    except (IndexError, AttributeError, TypeError):
        return None


def main(
    payload: Dict[str, Any],
    headers: Dict[str, Any] | None = None,
    pg_resource: Dict[str, Any] | None = None,
    ycloud_secret: str | None = None,
) -> Dict[str, Any]:
    headers = headers or {}
    if not isinstance(payload, dict):
        return InboundResult(ok=False, error="invalid_payload").__dict__
    if not pg_resource:
        return InboundResult(ok=False, error="missing_pg_resource").__dict__

    if _should_require_signature(ycloud_secret):
        sig_header = headers.get("x-ycloud-signature") or headers.get("X-YCloud-Signature") or ""
        ts, v1 = _parse_signature_header(sig_header)
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        if not (ycloud_secret and ts and v1 and verify_signature(ycloud_secret, body, v1, ts)):
            return InboundResult(ok=False, error="invalid_signature").__dict__

    msg = _extract_message(payload)
    if not msg:
        return InboundResult(ok=True, action="NO_MESSAGES").__dict__

    frm = msg.get("from")
    msg_id = msg.get("id")
    msg_type = msg.get("type")
    timestamp = msg.get("timestamp")

    phone_norm = normalize_phone_e164_mx(frm)
    if not phone_norm:
        return InboundResult(ok=False, error="invalid_phone").__dict__

    contact_name = (
        payload.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("contacts", [{}])[0]
        .get("profile", {})
        .get("name")
    )

    upsert_res = upsert_lead(
        {
            "phone": frm,
            "phone_normalized": phone_norm,
            "name": contact_name,
        },
        pg_resource,
    )
    if not upsert_res.get("success"):
        return InboundResult(ok=False, error=upsert_res.get("error", "upsert_failed")).__dict__

    lead_id = upsert_res["lead_id"]
    text_body = ""
    if msg_type == "text":
        text_body = (msg.get("text", {}).get("body") or "").strip().lower()

    conn = None
    action = "STORED"
    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ek_ycloud_messages (
                    ycloud_message_id, lead_id, direction, message_type, content, status, sent_at
                ) VALUES (%s, %s, 'inbound', %s, %s::jsonb, 'accepted', to_timestamp(%s::double precision))
                ON CONFLICT (ycloud_message_id) DO NOTHING
                """,
                (msg_id, lead_id, msg_type, Json(msg), timestamp or 0),
            )

            if text_body in ("stop", "baja", "unsubscribe"):
                cur.execute("UPDATE ek_leads SET stage = 'UNSUBSCRIBED', updated_at = NOW() WHERE lead_id = %s", (lead_id,))
                action = "UNSUBSCRIBE"
            elif "ya pag" in text_body or "pague" in text_body or "pague" in text_body:
                cur.execute(
                    """
                    INSERT INTO ek_sales (lead_id, status, provider, proof)
                    VALUES (%s, 'claimed', 'vitalhealth', %s::jsonb)
                    """,
                    (lead_id, Json({"source": "whatsapp_inbound", "message_id": msg_id})),
                )
                cur.execute("UPDATE ek_leads SET score = score + 50, updated_at = NOW() WHERE lead_id = %s", (lead_id,))
                action = "PAYMENT_CLAIM"

            cur.execute(
                """
                INSERT INTO ek_lead_events (lead_id, event_type, payload)
                VALUES (%s, 'ycloud_inbound_message', %s::jsonb)
                """,
                (lead_id, Json({"message_id": msg_id, "message_type": msg_type, "action": action})),
            )

        conn.commit()
        return InboundResult(ok=True, lead_id=str(lead_id), action=action).__dict__
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("Error processing inbound webhook")
        return InboundResult(ok=False, error=str(exc)).__dict__
    finally:
        if conn:
            conn.close()
