"""Execute scheduled jobs and dispatch WhatsApp templates."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

import psycopg2
from psycopg2.extras import RealDictCursor
import yaml

from .ycloud_send_template import main as ycloud_send_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def load_templates_config() -> Dict[str, Any]:
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "../../../resources/einstein_kids/templates.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle) or {}
        return data.get("templates", {})
    except Exception as exc:
        logger.error("Failed to load templates config: %s", exc)
        return {}


def get_template_info(job_type: str, avatar: str, templates_config: Dict[str, Any]) -> Dict[str, Any] | None:
    suffix = "moms" if avatar == "mother" else "therapists"
    by_avatar = f"{job_type}_{suffix}"
    if by_avatar in templates_config:
        return templates_config[by_avatar]
    if job_type in templates_config:
        return templates_config[job_type]
    return None


def _build_params(job: Dict[str, Any], required_params: list[str]) -> list[str]:
    out: list[str] = []
    lead_name = (job.get("name") or "").strip()
    event_start_at = job.get("event_start_at")
    for param in required_params:
        if param == "first_name":
            out.append(lead_name.split(" ")[0] if lead_name else "Cliente")
        elif param == "event_date":
            out.append(event_start_at.strftime("%d/%m") if event_start_at else "TBD")
        elif param == "event_time":
            out.append(event_start_at.strftime("%H:%M") if event_start_at else "TBD")
        else:
            out.append("")
    return out


def main(pg_resource: Dict[str, Any] | None = None, batch_size: int = 50) -> Dict[str, Any]:
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    templates_config = load_templates_config()
    if not templates_config:
        return {"ok": False, "error": "templates_config_missing"}

    conn = None
    executed = 0
    failed = 0
    cancelled = 0

    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    j.job_id,
                    j.lead_id,
                    j.job_type,
                    j.run_at,
                    j.attempts,
                    l.phone_normalized,
                    l.avatar,
                    l.name,
                    l.event_start_at
                FROM ek_jobs j
                JOIN ek_leads l ON j.lead_id = l.lead_id
                WHERE j.status = 'scheduled'
                  AND j.run_at <= NOW()
                  AND j.attempts < %s
                ORDER BY j.run_at ASC
                LIMIT %s
                FOR UPDATE OF j SKIP LOCKED
                """,
                (MAX_ATTEMPTS, batch_size),
            )
            jobs = cur.fetchall()

            for job in jobs:
                job_id = job["job_id"]
                attempts = int(job.get("attempts", 0))

                template_info = get_template_info(job["job_type"], job.get("avatar", "mother"), templates_config)
                if not template_info:
                    attempts += 1
                    status = "failed" if attempts >= MAX_ATTEMPTS else "scheduled"
                    cur.execute(
                        """
                        UPDATE ek_jobs
                        SET attempts = %s, status = %s, last_error = %s, updated_at = NOW()
                        WHERE job_id = %s
                        """,
                        (attempts, status, "template_not_found", job_id),
                    )
                    failed += 1
                    continue

                params = _build_params(job, template_info.get("params", []))
                result = ycloud_send_template(
                    lead_id=str(job["lead_id"]),
                    template_name=template_info["name"],
                    language=template_info.get("language", "es_MX"),
                    params=params,
                    pg_resource=pg_resource,
                )

                if result.get("ok"):
                    cur.execute(
                        "UPDATE ek_jobs SET status = 'sent', updated_at = NOW() WHERE job_id = %s",
                        (job_id,),
                    )
                    executed += 1
                    continue

                attempts += 1
                status = "failed" if attempts >= MAX_ATTEMPTS else "scheduled"
                if status == "failed":
                    cancelled += 1
                cur.execute(
                    """
                    UPDATE ek_jobs
                    SET attempts = %s, status = %s, last_error = %s, updated_at = NOW()
                    WHERE job_id = %s
                    """,
                    (attempts, status, result.get("error", "send_failed"), job_id),
                )
                failed += 1

        conn.commit()
        return {
            "ok": True,
            "executed": executed,
            "failed": failed,
            "failed_final": cancelled,
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("job_runner_cron failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
