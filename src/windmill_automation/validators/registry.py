import json
from typing import Any, Dict, Optional


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_schema_path(event_name: Optional[str]) -> Optional[str]:
    if not event_name:
        return None
    registry = load_json("contracts/registry.json")
    return registry.get(event_name)
