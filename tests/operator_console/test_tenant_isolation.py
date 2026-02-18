from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def test_tenant_isolation_smoke(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "operator_console.db"
    monkeypatch.setenv("OPERATOR_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OPERATOR_ENV", "dev")
    monkeypatch.setenv("OPERATOR_ADMIN_USER", "admin")
    monkeypatch.setenv("OPERATOR_ADMIN_PASSWORD", "change_me")
    monkeypatch.setenv("OPERATOR_JWT_SECRET", "test_secret_1234567890")

    db = importlib.import_module("apps.operator_console.app.db")
    models = importlib.import_module("apps.operator_console.app.models")
    auth = importlib.import_module("apps.operator_console.app.auth")
    importlib.reload(db)
    importlib.reload(models)
    importlib.reload(auth)
    module = importlib.import_module("apps.operator_console.app.main")
    module = importlib.reload(module)
    client = TestClient(module.app)

    login = client.post("/api/auth/login", json={"username": "admin", "password": "change_me"})
    token = login.json()["access_token"]

    headers_cyn = {"Authorization": f"Bearer {token}", "X-Operator-Tenant": "cyn"}
    headers_other = {"Authorization": f"Bearer {token}", "X-Operator-Tenant": "other"}

    create = client.post(
        "/api/clients",
        headers=headers_cyn,
        json={"name": "Cyn Workspace", "industry": "education", "owner": "ops", "status": "active"},
    )
    assert create.status_code == 200

    summary_cyn = client.get("/api/summary", headers=headers_cyn).json()
    summary_other = client.get("/api/summary", headers=headers_other).json()
    assert summary_cyn["clients"] == 1
    assert summary_other["clients"] == 0
