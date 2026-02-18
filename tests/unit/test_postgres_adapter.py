from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from windmill_automation.adapters.postgres_adapter import DockerPostgresAdapter
from windmill_automation.ports.persistence import AuditRecord


@pytest.fixture
def adapter() -> DockerPostgresAdapter:
    return DockerPostgresAdapter(dsn="postgresql://user:pass@localhost:5432/test")


def _mock_conn_cursor():
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__.return_value = None

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    return mock_conn, mock_cursor


def test_record_audit_log_success(adapter: DockerPostgresAdapter) -> None:
    record = AuditRecord(actor="test_user", action="test_action", details={"foo": "bar"}, trace_id="trace_123")
    mock_conn, mock_cursor = _mock_conn_cursor()

    with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
        adapter.record_audit_log(record)

    assert mock_connect.called
    assert mock_cursor.execute.called
    sql = mock_cursor.execute.call_args.args[0]
    assert "INSERT INTO audit_log" in sql


def test_record_audit_log_failure(adapter: DockerPostgresAdapter) -> None:
    record = AuditRecord(actor="u", action="a", details={})

    with patch("psycopg2.connect", side_effect=RuntimeError("DB Error")):
        with pytest.raises(RuntimeError, match="Error ejecutando SQL"):
            adapter.record_audit_log(record)


def test_get_audit_logs_parsing(adapter: DockerPostgresAdapter) -> None:
    mock_conn, mock_cursor = _mock_conn_cursor()
    mock_cursor.fetchall.return_value = [{"actor": "me", "action": "x"}]

    with patch("psycopg2.connect", return_value=mock_conn):
        logs = adapter.get_audit_logs(limit=10)

    assert logs == [{"actor": "me", "action": "x"}]
