from __future__ import annotations

import importlib
import os

import pytest


def test_production_rejects_default_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_ENV", "production")
    monkeypatch.setenv("OPERATOR_JWT_SECRET", "change_me_now")
    monkeypatch.setenv("OPERATOR_ADMIN_PASSWORD", "change_me")
    monkeypatch.setenv("OPERATOR_DB_URL", "sqlite:///:memory:")
    with pytest.raises(RuntimeError, match="Insecure production configuration"):
        db = importlib.import_module("apps.operator_console.app.db")
        models = importlib.import_module("apps.operator_console.app.models")
        auth = importlib.import_module("apps.operator_console.app.auth")
        importlib.reload(db)
        importlib.reload(models)
        importlib.reload(auth)
        module = importlib.import_module("apps.operator_console.app.main")
        importlib.reload(module)


def test_dev_allows_default_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_ENV", "dev")
    monkeypatch.setenv("OPERATOR_JWT_SECRET", "change_me_now")
    monkeypatch.setenv("OPERATOR_ADMIN_PASSWORD", "change_me")
    monkeypatch.setenv("OPERATOR_DB_URL", "sqlite:///:memory:")
    db = importlib.import_module("apps.operator_console.app.db")
    models = importlib.import_module("apps.operator_console.app.models")
    auth = importlib.import_module("apps.operator_console.app.auth")
    importlib.reload(db)
    importlib.reload(models)
    importlib.reload(auth)
    module = importlib.import_module("apps.operator_console.app.main")
    importlib.reload(module)
    assert os.getenv("OPERATOR_ENV") == "dev"


def test_production_requires_endpoint_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_ENV", "production")
    monkeypatch.setenv("OPERATOR_JWT_SECRET", "supersecure_secret_value_1234567890")
    monkeypatch.setenv("OPERATOR_ADMIN_PASSWORD", "very_secure_password_123")
    monkeypatch.setenv("OPERATOR_DB_URL", "sqlite:///:memory:")
    monkeypatch.delenv("OPERATOR_ALLOWED_ENDPOINT_HOSTS", raising=False)

    db = importlib.import_module("apps.operator_console.app.db")
    models = importlib.import_module("apps.operator_console.app.models")
    auth = importlib.import_module("apps.operator_console.app.auth")
    importlib.reload(db)
    importlib.reload(models)
    importlib.reload(auth)
    with pytest.raises(RuntimeError, match="OPERATOR_ALLOWED_ENDPOINT_HOSTS is required"):
        module = importlib.import_module("apps.operator_console.app.main")
        importlib.reload(module)
