"""
Windmill script: M20_no_show_sequence.py (Moms)
Triggered if attendance_minutes < 25% (Drop-off or No-Show).
Strategy: Stealth / Value (Send Summary PDF/Link).
"""
from __future__ import annotations
import logging
from ..shared.ycloud_send_template import main as send_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(
    lead_id: str,
    pg_resource: dict = None
) -> dict:
    
    # 1. Send "Stealth" Summary Template
    # Template: EK_MOMS_NO_SHOW_STEALTH
    # Content idea: "Hola [Name], aquí te dejo el resumen de los 3 puntos clave de hoy..."
    
    # We assume this template exists in templates.yaml map
    res_msg = send_template(
        lead_id=lead_id,
        template_name="EK_MOMS_NO_SHOW_STEALTH", 
        pg_resource=pg_resource
    )
    
    return {
        "ok": res_msg["ok"],
        "action": "sent_stealth_summary"
    }
