import json
import sys
from typing import Any, Dict


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def type_matches(value: Any, expected_type: str) -> bool:
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


def validate_object(schema: Dict[str, Any], data: Dict[str, Any], path: str = "") -> Dict[str, Any]:
    errors = []

    required = schema.get("required", [])
    for key in required:
        if key not in data:
            errors.append(f"{path}{key}: faltante (required)")

    properties = schema.get("properties", {})
    for key, prop in properties.items():
        if key in data:
            value = data[key]
            t = prop.get("type")
            if t and not type_matches(value, t):
                errors.append(f"{path}{key}: tipo inválido (esperado {t})")
            if t == "array":
                items_schema = prop.get("items")
                if items_schema:
                    for idx, item in enumerate(value):
                        if items_schema.get("type") == "object":
                            sub = validate_object(items_schema, item, path=f"{path}{key}[{idx}].")
                            errors.extend(sub.get("errors", []))
                        else:
                            it = items_schema.get("type")
                            if it and not type_matches(item, it):
                                errors.append(f"{path}{key}[{idx}]: tipo inválido (esperado {it})")
                min_items = prop.get("minItems")
                if isinstance(min_items, int) and len(value) < min_items:
                    errors.append(f"{path}{key}: minItems {min_items} no cumplido")
            if t == "object" and "properties" in prop:
                sub = validate_object(prop, value, path=f"{path}{key}.")
                errors.extend(sub.get("errors", []))
            if "minimum" in prop and isinstance(value, (int, float)) and value < prop["minimum"]:
                errors.append(f"{path}{key}: mínimo {prop['minimum']} no cumplido")
            if "const" in prop and value != prop["const"]:
                errors.append(f"{path}{key}: valor debe ser '{prop['const']}'")

    additional = schema.get("additionalProperties", True)
    if additional is False:
        extras = set(data.keys()) - set(properties.keys())
        for e in extras:
            errors.append(f"{path}{e}: propiedad no permitida (additionalProperties=false)")

    return {"valid": len(errors) == 0, "errors": errors}


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/core/validate_event.py <ruta_schema.json> <ruta_data.json>")
        sys.exit(2)
    schema_path = sys.argv[1]
    data_path = sys.argv[2]
    schema = load_json(schema_path)
    data = load_json(data_path)
    result = validate_object(schema, data)
    if result["valid"]:
        print("OK: payload válido")
        sys.exit(0)
    else:
        print("ERROR: payload inválido")
        for e in result["errors"]:
            print(f"- {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
