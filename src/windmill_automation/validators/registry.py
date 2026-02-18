from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_schema_path(event_name: Optional[str]) -> Optional[str]:
    if not event_name:
        return None
    repo_root = Path(__file__).resolve().parents[3]
    registry = load_json(str(repo_root / "contracts" / "registry.json"))
    schema_rel = registry.get(event_name)
    if not schema_rel:
        return None
    return str(repo_root / schema_rel)
