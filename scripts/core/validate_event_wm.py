import json
import sys
import uuid
from typing import Any, Dict

from validate_event import load_json, validate_object
from scripts.lib.json_logging import log_json


def ensure_trace_id(payload: Dict[str, Any]) -> str:
    tid = payload.get("trace_id")
    if isinstance(tid, str) and tid.strip():
        return tid
    return f"trace_{uuid.uuid4().hex}"


def main():
    if len(sys.argv) < 2:
        log_json(
            "error",
            "Uso incorrecto de validate_event_wm",
            trace_id=None,
            extra={"hint": "Uso: validate_event_wm <ruta_payload.json> o '-' (stdin)"},
        )
        print(json.dumps({"valid": False, "errors": ["Uso: validate_event_wm <ruta_payload.json> o '-' (stdin)"], "trace_id": None}))
        sys.exit(2)

    # Cargar payload
    arg = sys.argv[1]
    if arg == "-":
        payload = json.load(sys.stdin)
    else:
        payload = load_json(arg)

    trace_id = ensure_trace_id(payload)
    event_id = payload.get("event_id")
    source = payload.get("metadata", {}).get("source")
    log_json(
        "info",
        "Inicio de validación de evento",
        trace_id=trace_id,
        event_id=event_id,
        source=source,
        workflow_id="mvp_ingesta_validacion_orquestacion",
        status="received",
    )

    # Seleccionar esquema según event_name
    registry = load_json("contracts/registry.json")
    event_name = payload.get("event_name")
    schema_path = registry.get(event_name)
    if not schema_path:
        out = {"valid": False, "errors": [f"Evento no registrado: {event_name}"], "trace_id": trace_id}
        log_json(
            "error",
            "Evento no registrado",
            trace_id=trace_id,
            event_id=event_id,
            source=source,
            error_code="schema_not_found",
            reason=f"Evento no registrado: {event_name}",
            workflow_id="mvp_ingesta_validacion_orquestacion",
            status="failed",
        )
        print(json.dumps(out))
        sys.exit(1)

    schema = load_json(schema_path)
    result = validate_object(schema, payload)
    out = {"valid": result["valid"], "errors": result["errors"], "trace_id": trace_id}
    log_json(
        "info" if result["valid"] else "warn",
        "Resultado de validación de evento",
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
