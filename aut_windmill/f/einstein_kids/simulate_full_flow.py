"""
Windmill script: simulate_full_flow.py
Testing tool to simulate the entire lifecycle of a lead (Moms Funnel).
"""
import logging
import time
import json
import os
import sys
import uuid
from datetime import datetime, timedelta

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import flows - specific import style for running as script vs module
try:
    from shared.ycloud_webhook_inbound import main as webhook_inbound
    from shared.schedule_jobs import main as schedule_jobs
    from shared.job_runner_cron import main as job_runner
    from moms.M10_pre_event_sequence import main as m10_pre_event
    from moms.M20_no_show_sequence import main as m20_no_show
except ImportError:
    # Fallback for relative imports if run as module
    from .shared.ycloud_webhook_inbound import main as webhook_inbound
    from .shared.schedule_jobs import main as schedule_jobs
    from .shared.job_runner_cron import main as job_runner
    from .moms.M10_pre_event_sequence import main as m10_pre_event
    from .moms.M20_no_show_sequence import main as m20_no_show

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Env Vars for Testing if not set
os.environ["YCLOUD_API_KEY"] = "placeholder_key" 
os.environ["YCLOUD_SENDER"] = "5215512345678"

def main(pg_resource: dict = None):
    # Setup PG Resource from Env if not provided
    if not pg_resource:
        pg_resource = {
            "host": os.getenv("PGHOST", "localhost"),
            "port": os.getenv("PGPORT", "5432"),
            "user": os.getenv("PGUSER", "postgres"),
            "password": os.getenv("PGPASSWORD", "password"),
            "dbname": os.getenv("PGDATABASE", "postgres")
        }
        
    print(f"--- STARTING FULL FLOW SIMULATION (DB: {pg_resource['host']}:{pg_resource['port']}) ---")
    
    # 1. Simulate YCloud Webhook (New Lead Opt-in via WhatsApp?)
    # Or just manual opt-in. Let's use webhook with "Hola" to create lead.
    # Actually, webhook inbound creates lead if not exists.
    
    test_phone = f"52155{int(time.time())}" # Unique phone
    print(f"1. Simulating Webhook Inbound for phone {test_phone}...")
    
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": test_phone,
                        "id": f"wamid.{uuid.uuid4()}",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": "Hola, quiero info de la masterclass"}
                    }],
                    "contacts": [{"profile": {"name": "Test Mom"}}]
                }
            }]
        }]
    }
    
    res_webhook = webhook_inbound(payload=payload, pg_resource=pg_resource)
    print(f"   Webhook Result: {res_webhook}")
    
    if not res_webhook["ok"]:
        return {"error": "Webhook failed"}
        
    lead_id = res_webhook["lead_id"]
    print(f"   Lead Created/Found: {lead_id}")
    
    # 2. Trigger Pre-Event Sequence (M10)
    # Usually triggered by matching event or explicit flow.
    # Let's say lead opted in for an event starting in 2 days.
    # We update lead event_start_at first.
    
    import psycopg2
    conn = psycopg2.connect(**pg_resource)
    cur = conn.cursor()
    
    event_start = datetime.utcnow() + timedelta(days=2)
    cur.execute("UPDATE ek_leads SET event_start_at = %s, avatar = 'mother' WHERE lead_id = %s", (event_start, lead_id))
    conn.commit()
    conn.close()
    
    print(f"2. Triggering M10 (Pre-Event) for lead {lead_id}...")
    res_m10 = m10_pre_event(lead_id=lead_id, event_start_at=event_start.isoformat(), pg_resource=pg_resource)
    print(f"   M10 Result: {res_m10}")
    
    # 3. Verify Scheduled Jobs
    print("3. Verifying DB for scheduled jobs...")
    conn = psycopg2.connect(**pg_resource)
    cur = conn.cursor()
    cur.execute("SELECT job_type, run_at, status FROM ek_jobs WHERE lead_id = %s", (lead_id,))
    jobs = cur.fetchall()
    conn.close()
    
    for j in jobs:
        print(f"   - Job: {j[0]} at {j[1]} status: {j[2]}")
        
    # 4. Run Cron (Simulate Time Travel?)
    # We can't easily time travel in DB. But we can force run for testing if we manually update run_at.
    # Let's verify 'welcome' job (run_at=Now-ish) is picked up.
    
    print("4. Running Job Runner Cron (should pick up 'welcome')...")
    res_cron = job_runner(pg_resource=pg_resource)
    print(f"   Cron Result: {res_cron}")
    
    # 5. Simulate "Stealth" No-Show (M20)
    print("5. Simulating Stealth No-Show (Post Event)...")
    res_m20 = m20_no_show(lead_id=lead_id, pg_resource=pg_resource)
    print(f"   M20 Result: {res_m20}")

    print("--- SIMULATION COMPLETE ---")
    return {
        "lead_id": lead_id,
        "phone": test_phone,
        "cron_stats": res_cron,
        "m20_stats": res_m20
    }

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Simulation Failed: {e}")
