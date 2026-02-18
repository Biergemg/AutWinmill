import json
from typing import Any, Dict, List, Tuple


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float))
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return True


def _validate_object(schema: Dict[str, Any], data: Dict[str, Any], path: str = "") -> Tuple[bool, List[str]]:
    errors: List[str] = []

    required = schema.get("required", [])
    for key in required:
        if key not in data:
            errors.append(f"{path}{key}: faltante (required)")

    properties = schema.get("properties", {})
    for key, prop in properties.items():
        if key in data:
            value = data[key]
            t = prop.get("type")
            if t and not _type_matches(value, t):
                errors.append(f"{path}{key}: tipo inválido (esperado {t})")
            if t == "array":
                items_schema = prop.get("items")
                if items_schema:
                    for idx, item in enumerate(value):
                        if items_schema.get("type") == "object":
                            sub_valid, sub_errors = _validate_object(items_schema, item, path=f"{path}{key}[{idx}].")
                            if not sub_valid:
                                errors.extend(sub_errors)
                        else:
                            it = items_schema.get("type")
                            if it and not _type_matches(item, it):
                                errors.append(f"{path}{key}[{idx}]: tipo inválido (esperado {it})")
                min_items = prop.get("minItems")
                if isinstance(min_items, int) and len(value) < min_items:
                    errors.append(f"{path}{key}: minItems {min_items} no cumplido")
            if t == "object" and "properties" in prop:
                sub_valid, sub_errors = _validate_object(prop, value, path=f"{path}{key}.")
                if not sub_valid:
                    errors.extend(sub_errors)
            if "minimum" in prop and isinstance(value, (int, float)) and value < prop["minimum"]:
                errors.append(f"{path}{key}: mínimo {prop['minimum']} no cumplido")
            if "const" in prop and value != prop["const"]:
                errors.append(f"{path}{key}: valor debe ser '{prop['const']}'")

    additional = schema.get("additionalProperties", True)
    if additional is False:
        extras = set(data.keys()) - set(properties.keys())
        for e in extras:
            errors.append(f"{path}{e}: propiedad no permitida (additionalProperties=false)")

    return (len(errors) == 0, errors)
