import json
import sys
import os
import uuid
from typing import Any, Dict

# Configurar path para imports - debe ir ANTES de importar módulos locales
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
src_path = os.path.join(project_root, "src")

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from scripts.lib.json_logging import log_json
from windmill_automation.validators.jsonschema_validator import validate_payload


def ensure_trace_id(payload: Dict[str, Any]) -> str:
    tid = payload.get("trace_id")
    if isinstance(tid, str) and tid.strip():
        return tid
    return f"trace_{uuid.uuid4().hex}"


def main():
    if len(sys.argv) < 2:
        log_json(
            "error",
            "Uso incorrecto de validate_event_strategy",
            trace_id=None,
            extra={"hint": "Uso: validate_event_strategy <ruta_payload.json> o '-' (stdin)"},
        )
        print(json.dumps({"valid": False, "errors": ["Uso: validate_event_strategy <ruta_payload.json> o '-' (stdin)"], "trace_id": None}))
        sys.exit(2)

    arg = sys.argv[1]
    if arg == "-":
        payload = json.load(sys.stdin)
    else:
        with open(arg, "r", encoding="utf-8") as f:
            payload = json.load(f)

    trace_id = ensure_trace_id(payload)
    event_id = payload.get("event_id")
    source = payload.get("metadata", {}).get("source")
    log_json(
        "info",
        "Inicio de validación (Strategy) de evento",
        trace_id=trace_id,
        event_id=event_id,
        source=source,
        workflow_id="mvp_ingesta_validacion_orquestacion",
        status="received",
    )

    result = validate_payload(payload)
    out = {"valid": result["valid"], "errors": result["errors"], "trace_id": trace_id}
    log_json(
        "info" if result["valid"] else "warn",
        "Resultado de validación (Strategy)",
        trace_id=trace_id,
        event_id=event_id,
        source=source,
        workflow_id="mvp_ingesta_validacion_orquestacion",
        status="validated" if result["valid"] else "failed",
        extra={"errors": result["errors"]},
    )
    print(json.dumps(out))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
