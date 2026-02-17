import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock
from windmill_automation.adapters.postgres_adapter import DockerPostgresAdapter
from windmill_automation.ports.persistence import AuditRecord

@pytest.fixture
def adapter():
    return DockerPostgresAdapter()

def test_record_audit_log_success(adapter):
    record = AuditRecord(
        actor="test_user",
        action="test_action",
        details={"foo": "bar"},
        trace_id="trace_123"
    )
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        
        adapter.record_audit_log(record)
        
        assert mock_run.called
        args, kwargs = mock_run.call_args
        cmd_list = args[0]
        assert "docker" in cmd_list
        assert "INSERT INTO audit_log" in cmd_list[-1]

def test_record_audit_log_failure(adapter):
    record = AuditRecord(actor="u", action="a", details={})
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["cmd"], stderr="DB Error")
        
        with pytest.raises(RuntimeError, match="Error ejecutando SQL"):
            adapter.record_audit_log(record)

def test_get_audit_logs_parsing(adapter):
    sample_data = [{"id": 1, "actor": "me"}]
    json_output = json.dumps(sample_data)
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = json_output
        mock_run.return_value.returncode = 0
        
        logs = adapter.get_audit_logs()
        assert logs == sample_data
