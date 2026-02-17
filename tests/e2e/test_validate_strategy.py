import json
import subprocess


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def test_validate_strategy_valid():
    code, out, err = run(["python", "scripts/core/validate_event_strategy.py", "contracts/examples/order_created.valid.json"])
    assert code == 0
    parsed = json.loads(out)
    assert parsed["valid"] is True
    assert parsed["trace_id"]


def test_validate_strategy_invalid():
    code, out, err = run(["python", "scripts/core/validate_event_strategy.py", "contracts/examples/order_created.invalid.json"])
    assert code != 0
    parsed = json.loads(out)
    assert parsed["valid"] is False
    assert isinstance(parsed["errors"], list) and len(parsed["errors"]) > 0
