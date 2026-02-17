import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from windmill_automation.validators.jsonschema_validator import validate_payload


def test_order_created_valid():
    with open("contracts/examples/order_created.valid.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    result = validate_payload(payload)
    assert result["valid"] is True
    assert result["errors"] == []


def test_order_created_invalid():
    with open("contracts/examples/order_created.invalid.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    result = validate_payload(payload)
    assert result["valid"] is False
    assert isinstance(result["errors"], list) and len(result["errors"]) > 0
