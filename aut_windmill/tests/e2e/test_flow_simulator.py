import pytest
import json
from unittest.mock import MagicMock, patch
from windmill_automation.validators.jsonschema_validator import validate_payload
from windmill_automation.adapters.postgres_adapter import DockerPostgresAdapter
from windmill_automation.adapters.windmill_adapter import EnvWindmillAdapter
from windmill_automation.ports.persistence import AuditRecord

# Simula el paso: validate_contract
def step_validate_contract(payload):
    result = validate_payload(payload)
    if not result["valid"]:
        raise ValueError(f"Validation failed: {result['errors']}")
    return {"trace_id": payload.get("trace_id", "trace_new"), "errors": []}

# Simula el paso: audit_validated
def step_audit_validated(trace_id, event_id, db_adapter):
    record = AuditRecord(
        actor="system",
        action="validated",
        details={},
        trace_id=trace_id,
        workflow_id="mvp_flow",
        event_id=event_id
    )
    db_adapter.record_audit_log(record)

# Test E2E del Flujo Lógico
def test_flow_mvp_execution_success():
    # 1. Setup Inputs
    with open("contracts/examples/order_created.valid.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # 2. Setup Adapters (Mocks)
    db_adapter = DockerPostgresAdapter()
    db_adapter.record_audit_log = MagicMock() # Mock DB calls
    
    wm_adapter = EnvWindmillAdapter()
    
    # 3. Simulate Flow Steps
    # Step: validate_contract
    val_output = step_validate_contract(payload)
    assert val_output["errors"] == []
    
    # Step: audit_validated
    step_audit_validated(val_output["trace_id"], payload["event_id"], db_adapter)
    
    # 4. Verify Outcomes
    # Verify Audit Log was recorded
    assert db_adapter.record_audit_log.called
    call_args = db_adapter.record_audit_log.call_args[0][0]
    assert call_args.action == "validated"
    assert call_args.event_id == payload["event_id"]

def test_flow_mvp_execution_failure():
    # 1. Setup Invalid Input
    with open("contracts/examples/order_created.invalid.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    # 2. Simulate Flow
    with pytest.raises(ValueError, match="Validation failed"):
        step_validate_contract(payload)
    
    # Flow stops or goes to DLQ (logic branch)
