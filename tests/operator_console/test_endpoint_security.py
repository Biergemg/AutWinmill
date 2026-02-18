from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient


class _FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text
        self.ok = 200 <= status_code < 300


def _load_app(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "operator_console_endpoint.db"
    monkeypatch.setenv("OPERATOR_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("OPERATOR_ENV", "dev")
    monkeypatch.setenv("OPERATOR_ADMIN_USER", "admin")
    monkeypatch.setenv("OPERATOR_ADMIN_PASSWORD", "change_me")
    monkeypatch.setenv("OPERATOR_JWT_SECRET", "test_secret_endpoint_1234567890")
    monkeypatch.setenv("OPERATOR_ALLOWED_ENDPOINT_HOSTS", "windmill-cyn,allowed.local")
    monkeypatch.setenv("OPERATOR_TOKEN_TARGET_HOSTS", "windmill-cyn")
    monkeypatch.setenv("WINDMILL_API_TOKEN", "wm_secret")

    db = importlib.import_module("apps.operator_console.app.db")
    models = importlib.import_module("apps.operator_console.app.models")
    auth = importlib.import_module("apps.operator_console.app.auth")
    importlib.reload(db)
    importlib.reload(models)
    importlib.reload(auth)
    module = importlib.import_module("apps.operator_console.app.main")
    module = importlib.reload(module)
    return module, TestClient(module.app)


def test_endpoint_allowlist_and_token_scoping(monkeypatch, tmp_path: Path) -> None:
    module, client = _load_app(monkeypatch, tmp_path)
    login = client.post("/api/auth/login", json={"username": "admin", "password": "change_me"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Operator-Tenant": "cyn"}

    created_client = client.post(
        "/api/clients",
        headers=headers,
        json={"name": "Cyn Endpoint", "industry": "education", "owner": "ops", "status": "active"},
    )
    assert created_client.status_code == 200
    client_id = created_client.json()["id"]

    blocked = client.post(
        "/api/automations",
        headers=headers,
        json={
            "client_id": client_id,
            "name": "Blocked Endpoint",
            "channel": "mixed",
            "status": "active",
            "run_endpoint": "https://evil.example.com/hook",
            "http_method": "POST",
            "payload_template": "{}",
        },
    )
    assert blocked.status_code == 400

    auth_seen: list[str | None] = []

    def fake_request(method: str, url: str, headers: dict[str, str], json: dict[str, object], timeout: int):
        auth_seen.append(headers.get("Authorization"))
        return _FakeResponse()

    monkeypatch.setattr(module.requests, "request", fake_request)

    wm_auto = client.post(
        "/api/automations",
        headers=headers,
        json={
            "client_id": client_id,
            "name": "Windmill Endpoint",
            "channel": "mixed",
            "status": "active",
            "run_endpoint": "https://windmill-cyn/api/run",
            "http_method": "POST",
            "payload_template": "{}",
        },
    )
    assert wm_auto.status_code == 200
    wm_id = wm_auto.json()["id"]
    run_wm = client.post(f"/api/automations/{wm_id}/run", headers=headers, json={})
    assert run_wm.status_code == 200
    assert auth_seen[-1] == "Bearer wm_secret"

    allowed_auto = client.post(
        "/api/automations",
        headers=headers,
        json={
            "client_id": client_id,
            "name": "Allowed No Token",
            "channel": "mixed",
            "status": "active",
            "run_endpoint": "https://allowed.local/hook",
            "http_method": "POST",
            "payload_template": "{}",
        },
    )
    assert allowed_auto.status_code == 200
    allowed_id = allowed_auto.json()["id"]
    run_allowed = client.post(f"/api/automations/{allowed_id}/run", headers=headers, json={})
    assert run_allowed.status_code == 200
    assert auth_seen[-1] is None
