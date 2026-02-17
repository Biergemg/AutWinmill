"""
Windmill script: M10_pre_event_sequence.py (Moms)
Example Logic:
1. Send Welcome Message (Immediate)
2. Schedule Reminders (24h, 1h, 10m) - handled by schedule_jobs.py actually.

Wait, this script might be triggered by `lead.optin` flow.
Or maybe this script IS the flow that orchestration calls.

For this example, let's assume this script is called when lead matches 'mother' avatar and is new.
It sends the initial welcome and triggers scheduling.
"""
from __future__ import annotations
import logging
from ..shared.ycloud_send_template import main as send_template
from ..shared.schedule_jobs import main as schedule_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(
    lead_id: str,
    event_start_at: str,
    pg_resource: dict = None
) -> dict:
    
    # 1. Send Welcome Template
    # Template: EK_WELCOME_MOMS (defined in templates.yaml)
    # Params: [First Name (fetched inside sender)]
    res_msg = send_template(
        lead_id=lead_id,
        template_name="EK_WELCOME_MOMS", # Must match templates.yaml key or name mapping
        pg_resource=pg_resource
    )
    
    if not res_msg["ok"]:
        logger.error(f"Failed to send welcome: {res_msg}")
        # Continue to schedule anyway? Yes.

    # 2. Schedule Future Jobs
    res_sched = schedule_jobs(
        lead_id=lead_id,
        event_start_at=event_start_at,
        pg_resource=pg_resource
    )
    
    return {
        "ok": True,
        "welcome_sent": res_msg["ok"],
        "jobs_scheduled": res_sched.get("inserted", 0)
    }
