"""
Windmill script: ycloud_send_template.py
Sends a WhatsApp template message via YCloud API.
"""
from __future__ import annotations
import logging
import os
import json
import requests
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(
    lead_id: str,
    template_name: str,
    language: str = "es_MX",
    params: list = None,
    pg_resource: dict = None,
    ycloud_api_key: str = None,
    ycloud_sender: str = None
) -> dict:    
    # 0. Load Secrets/Env
    if not ycloud_api_key:
        ycloud_api_key = os.getenv("YCLOUD_API_KEY")
    if not ycloud_sender:
        ycloud_sender = os.getenv("YCLOUD_SENDER")
        
    if not ycloud_api_key or not ycloud_sender:
        
    if not ycloud_api_key:
        return {"ok": False, "error": "missing_ycloud_api_key"}

    conn = None
    try:
        conn = psycopg2.connect(**pg_resource)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch Lead Phone
        cur.execute("SELECT phone_normalized FROM ek_leads WHERE lead_id = %s", (lead_id,))
        lead = cur.fetchone()
        if not lead or not lead["phone_normalized"]:
            return {"ok": False, "error": "lead_not_found_or_no_phone"}
            
        to_phone = lead["phone_normalized"]
        
        # 2. Construct YCloud Payload
        # Mapping params to components
        components = []
        if params:
            parameters = []
            for p in params:
                parameters.append({"type": "text", "text": str(p)})
            components.append({"type": "body", "parameters": parameters})
            
        payload = {
            "from": ycloud_sender,
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components
            }
        }
        
        # 3. Send Request
        url = "https://api.ycloud.com/v2/whatsapp/messages/send"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": ycloud_api_key
        }
        
        status = "failed"
        ycloud_msg_id = None
        
        if "placeholder" in ycloud_api_key:
            logger.info(f"MOCK SEND to {to_phone}: {template_name}")
            ycloud_msg_id = f"mock_{int(datetime.now().timestamp())}"
            status = "accepted"
        else:
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"YCloud API Error: {resp.text}")
                return {"ok": False, "error": f"ycloud_api_error: {resp.status_code}", "detail": resp.text}
            
            data = resp.json()
            # YCloud response example: {"id": "..."} or {"messages": [{"id": "..."}]}
            ycloud_msg_id = data.get("id")
            if not ycloud_msg_id and "messages" in data:
                 ycloud_msg_id = data["messages"][0]["id"]
            
            status = "accepted"

        # 4. Log to DB
        cur.execute("""
            INSERT INTO ek_ycloud_messages (
                ycloud_message_id, lead_id, direction, message_type, template_name, content, status, sent_at
            ) VALUES (%s, %s, 'outbound', 'template', %s, %s, %s, NOW())
        """, (ycloud_msg_id, lead_id, template_name, json.dumps(payload), status))
        
        conn.commit()
        return {"ok": True, "ycloud_message_id": ycloud_msg_id}

    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Send Error: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        if conn: conn.close()

