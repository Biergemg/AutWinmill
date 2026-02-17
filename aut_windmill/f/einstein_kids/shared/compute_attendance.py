"""Compute attendance from Zoom events and update lead segmentation."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import psycopg2
from psycopg2.extras import Json, RealDictCursor
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_scoring_rules() -> Dict[str, int]:
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "../../../resources/einstein_kids/scoring.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle) or {}
        return data.get("rules", {})
    except Exception as exc:
        logger.error("Failed to load scoring rules: %s", exc)
        return {}


def _resolve_label(duration_minutes: int, total_duration_minutes: int) -> str:
    if duration_minutes <= 0:
        return "NO_SHOW"
    ratio = duration_minutes / max(total_duration_minutes, 1)
    if ratio < 0.25:
        return "DROP_OFF_EARLY"
    if ratio < 0.50:
        return "INTERESTED"
    if ratio < 0.90:
        return "HIGH_INTEREST"
    return "HOT_LEAD"


def _resolve_score_add(label: str, rules: Dict[str, int]) -> int:
    if label == "DROP_OFF_EARLY":
        return int(rules.get("video_view_25_percent", 10))
    if label == "INTERESTED":
        return int(rules.get("video_view_25_percent", 10))
    if label == "HIGH_INTEREST":
        return int(rules.get("video_view_50_percent", 40))
    if label == "HOT_LEAD":
        return int(rules.get("video_view_100_percent", 60))
    return 0


def main(
    meeting_id: str,
    total_duration_minutes: int = 90,
    pg_resource: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if not meeting_id:
        return {"ok": False, "error": "missing_meeting_id"}
    if not pg_resource:
        return {"ok": False, "error": "missing_pg_resource"}

    rules = load_scoring_rules()
    conn = None
    processed = 0

    try:
        conn = psycopg2.connect(**pg_resource)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    lead_id,
                    SUM(COALESCE((payload->>'duration_minutes')::int, 0)) AS duration_minutes
                FROM ek_lead_events
                WHERE event_type = 'zoom_participant_left'
                  AND payload->>'meeting_id' = %s
                GROUP BY lead_id
                """,
                (meeting_id,),
            )
            records = cur.fetchall()

            if not records:
                return {"ok": False, "error": "no_attendance_events_for_meeting", "meeting_id": meeting_id}

            for record in records:
                lead_id = record["lead_id"]
                duration = int(record["duration_minutes"] or 0)
                label = _resolve_label(duration, total_duration_minutes)
                score_add = _resolve_score_add(label, rules)

                if label == "HOT_LEAD":
                    cur.execute(
                        """
                        UPDATE ek_leads
                        SET score = score + %s,
                            stage = CASE WHEN stage != 'CUSTOMER' THEN 'HOT_LEAD' ELSE stage END,
                            updated_at = NOW()
                        WHERE lead_id = %s
                        """,
                        (score_add, lead_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE ek_leads
                        SET score = score + %s,
                            updated_at = NOW()
                        WHERE lead_id = %s
                        """,
                        (score_add, lead_id),
                    )

                cur.execute(
                    """
                    INSERT INTO ek_lead_events (lead_id, event_type, payload)
                    VALUES (%s, 'attendance_segment_computed', %s::jsonb)
                    """,
                    (
                        lead_id,
                        Json(
                            {
                                "meeting_id": meeting_id,
                                "duration_minutes": duration,
                                "segment": label,
                                "score_add": score_add,
                            }
                        ),
                    ),
                )
                processed += 1

        conn.commit()
        return {"ok": True, "meeting_id": meeting_id, "processed": processed}
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception("compute_attendance failed")
        return {"ok": False, "error": str(exc)}
    finally:
        if conn:
            conn.close()
