"""
Windmill script: schedule_jobs.py
Calculates and inserts future jobs based on event_start_at.
"""
from __future__ import annotations
import logging
import os
import yaml
from datetime import datetime, timedelta
import re

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_iso8601_duration(duration_str: str) -> timedelta:
    """
    Simple parser for ISO8601 durations like P1D, PT1H, -P2D.
    Does not support full standard (Y/M), focused on D/H/M/S.
    """
    if not duration_str:
        return timedelta(0)
    
    sign = 1
    if duration_str.startswith("-"):
        sign = -1
        duration_str = duration_str[1:]
        
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?')
    match = pattern.match(duration_str)
    if not match:
        return timedelta(0)
        
    parts = match.groupdict()
    kwargs = {k: float(v) for k, v in parts.items() if v}
    
    return timedelta(**kwargs) * sign

def main(
    lead_id: str,
    event_start_at: str,
    pg_resource: dict = None,
    schedules_config: dict = None # Option to pass config directly
) -> dict:
    
    if not event_start_at:
        return {"ok": False, "error": "missing_event_start_at"}
        
    # 1. Load configuration
    if not schedules_config:
        try:
            # Try loading relative file
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Adjust path to find resources/einstein_kids/schedules.yaml
            # Assuming flows/einstein_kids/shared/ -> ../../../resources/einstein_kids/schedules.yaml
            config_path = os.path.join(base_path, "../../../resources/einstein_kids/schedules.yaml")
            
            with open(config_path, 'r') as f:
                schedules_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load schedules.yaml: {e}")
            return {"ok": False, "error": f"config_load_error: {e}"}

    # 2. Parse Event Date
    try:
        # Normalize ISO string (Z -> +00:00)
        event_dt = datetime.fromisoformat(event_start_at.replace("Z", "+00:00"))
        now = datetime.now(event_dt.tzinfo) 
    except ValueError as e:
        return {"ok": False, "error": f"invalid_date_format: {e}"}

    # 3. Calculate Jobs
    # Logic: For masterclass_live, we have pre_event and post_event lists.
    # We schedule ALL of them. The runner will decide if they are valid at run time (or we filter here).
    # Actually, better to schedule them.
    
    jobs_to_insert = []
    
    # Assuming 'masterclass_live' is the default schedule key for now. 
    # In future, lead might have 'schedule_key' field.
    schedule_key = "masterclass_live" 
    schedule = schedules_config.get("schedules", {}).get(schedule_key, {})
    
    if not schedule:
        return {"ok": False, "error": "schedule_not_found"}

    # Process Pre-Event
    for item in schedule.get("pre_event", []):
        offset = parse_iso8601_duration(item["offset"])
        run_at = event_dt + offset
        
        # If run_at is in the past by a large margin (e.g. > 1 hour), maybe skip?
        # For now, schedule everything, let runner expire old jobs if needed.
        # Exception: "welcome" should be NOW if offset is 0? 
        # Actually schedule says PT0S, so it's exactly at event? No, logic is relative to event.
        # Wait, Welcome should be immediate upon signup. 
        # If schedules.yaml says offset PT0S relative to event, that means "AT EVENT START".
        # Welcome usually is immediate. 
        # Let's check schedules.yaml content again.
        # "welcome... offset: PT0S". This implies welcome happens AT the masterclass? That's wrong.
        # Usually welcome is offset from SIGNUP, not event.
        # BUT, the current implementation is "schedule_jobs" called likely at optin.
        # Let's special case "welcome": if job_type == 'welcome', run_at = NOW.
        
        if item["job_type"] == "welcome":
            run_at = datetime.now(event_dt.tzinfo)
        
        jobs_to_insert.append({
            "job_type": item["job_type"],
            "run_at": run_at,
            "status": "scheduled"
        })

    # Process Post-Event
    for item in schedule.get("post_event", []):
        offset = parse_iso8601_duration(item["offset"])
        run_at = event_dt + offset
        jobs_to_insert.append({
            "job_type": item["job_type"],
            "run_at": run_at,
            "status": "scheduled"
        })

    # 4. Write to DB
    conn = None
    inserted_count = 0
    try:
        conn = psycopg2.connect(**pg_resource)
        cur = conn.cursor()
        
        for job in jobs_to_insert:
            # Idempotency: Don't insert if same job_type exists for lead (regardless of status? maybe)
            # Or just ignore collisions if we had a unique constraint (we don't enforce one on job_type+lead_id in definitions, but we should logic it).
            
            cur.execute("""
                SELECT 1 FROM ek_jobs WHERE lead_id = %s AND job_type = %s
            """, (lead_id, job["job_type"]))
            
            if cur.fetchone():
                continue # Skip existing
                
            cur.execute("""
                INSERT INTO ek_jobs (lead_id, job_type, run_at, status)
                VALUES (%s, %s, %s, %s)
            """, (lead_id, job["job_type"], job["run_at"], job["status"]))
            inserted_count += 1
            
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"DB Error: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        if conn: conn.close()
        
    return {"ok": True, "inserted": inserted_count}
