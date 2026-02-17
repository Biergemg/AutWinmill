import json
from typing import Any, Dict, List, Tuple

from .base import _validate_object, load_json
from .registry import get_schema_path


def _validate_jsonschema(schema: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    try:
        import jsonschema
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(schema)
        errors = [f"{'.'.join(e.path)}: {e.message}" if e.path else f"schema: {e.message}" for e in validator.iter_errors(data)]
        return (len(errors) == 0, errors)
    except Exception:
        return (False, ["jsonschema_no_disponible"])


def validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_name = payload.get("event_name")
    schema_path = get_schema_path(event_name)
    if not schema_path:
        return {"valid": False, "errors": [f"Evento no registrado: {event_name}"]}
    schema = load_json(schema_path)

    ok, errors = _validate_jsonschema(schema, payload)
    if not ok and errors == ["jsonschema_no_disponible"]:
        ok2, errors2 = _validate_object(schema, payload)
        return {"valid": ok2, "errors": errors2}
    return {"valid": ok, "errors": errors}
