from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from .auth import assert_secure_runtime, create_token, require_user, verify_admin
from .db import bootstrap_schema, get_db
from .models import Automation, Client, Execution
from .schemas import (
    AutomationCreate,
    AutomationOut,
    ClientCreate,
    ClientOut,
    ExecutionOut,
    LoginRequest,
    RunRequest,
    SummaryOut,
    TokenResponse,
)

bootstrap_schema()
assert_secure_runtime()

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AutWinmill Operator Console", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
TENANT_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,79}$")
ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _csv_env_set(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


ALLOWED_ENDPOINT_HOSTS = _csv_env_set("OPERATOR_ALLOWED_ENDPOINT_HOSTS")
TOKEN_TARGET_HOSTS = _csv_env_set("OPERATOR_TOKEN_TARGET_HOSTS")


def _assert_runtime_network_policy() -> None:
    if os.getenv("OPERATOR_ENV", "dev").lower() not in {"prod", "production"}:
        return
    if not ALLOWED_ENDPOINT_HOSTS:
        raise RuntimeError("OPERATOR_ALLOWED_ENDPOINT_HOSTS is required in production")
    if TOKEN_TARGET_HOSTS and not TOKEN_TARGET_HOSTS.issubset(ALLOWED_ENDPOINT_HOSTS):
        raise RuntimeError("OPERATOR_TOKEN_TARGET_HOSTS must be a subset of OPERATOR_ALLOWED_ENDPOINT_HOSTS")


def _validate_run_endpoint(run_endpoint: str) -> tuple[str, str]:
    parsed = urlparse(run_endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="run_endpoint must use http or https")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="run_endpoint must include a valid host")
    host = parsed.hostname.lower()
    if ALLOWED_ENDPOINT_HOSTS and host not in ALLOWED_ENDPOINT_HOSTS:
        raise HTTPException(status_code=400, detail=f"run_endpoint host not allowed: {host}")
    return parsed.geturl(), host


_assert_runtime_network_policy()


def require_tenant(x_operator_tenant: str | None = Header(default=None, alias="X-Operator-Tenant")) -> str:
    default_tenant = os.getenv("OPERATOR_DEFAULT_TENANT") or "default"
    tenant = (x_operator_tenant or default_tenant).strip()
    if not TENANT_PATTERN.match(tenant):
        raise HTTPException(status_code=400, detail="Invalid tenant id")
    return tenant


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not verify_admin(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(payload.username))


@app.get("/api/summary", response_model=SummaryOut)
def summary(
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> SummaryOut:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    executions_24h = (
        db.query(func.count(Execution.id))
        .filter(Execution.tenant_id == tenant_id, Execution.created_at >= since)
        .scalar()
        or 0
    )
    success_24h = (
        db.query(func.count(Execution.id))
        .filter(Execution.tenant_id == tenant_id, Execution.created_at >= since, Execution.status == "success")
        .scalar()
        or 0
    )
    return SummaryOut(
        clients=db.query(func.count(Client.id)).filter(Client.tenant_id == tenant_id).scalar() or 0,
        automations=db.query(func.count(Automation.id)).filter(Automation.tenant_id == tenant_id).scalar() or 0,
        executions_24h=executions_24h,
        success_24h=success_24h,
    )


@app.get("/api/clients", response_model=list[ClientOut])
def list_clients(
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[Client]:
    return db.query(Client).filter(Client.tenant_id == tenant_id).order_by(Client.created_at.desc()).all()


@app.post("/api/clients", response_model=ClientOut)
def create_client(
    payload: ClientCreate,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> Client:
    exists = db.query(Client).filter(Client.tenant_id == tenant_id, Client.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Client already exists")
    entity = Client(tenant_id=tenant_id, **payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.put("/api/clients/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientCreate,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> Client:
    entity = db.query(Client).filter(Client.id == client_id, Client.tenant_id == tenant_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in payload.model_dump().items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity


@app.get("/api/automations", response_model=list[AutomationOut])
def list_automations(
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[Automation]:
    return db.query(Automation).filter(Automation.tenant_id == tenant_id).order_by(Automation.created_at.desc()).all()


@app.post("/api/automations", response_model=AutomationOut)
def create_automation(
    payload: AutomationCreate,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> Automation:
    method = payload.http_method.upper()
    if method not in ALLOWED_HTTP_METHODS:
        raise HTTPException(status_code=400, detail=f"http_method not allowed: {method}")
    endpoint, _ = _validate_run_endpoint(payload.run_endpoint)
    client = db.query(Client).filter(Client.id == payload.client_id, Client.tenant_id == tenant_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    payload_data = payload.model_dump()
    payload_data["http_method"] = method
    payload_data["run_endpoint"] = endpoint
    entity = Automation(tenant_id=tenant_id, **payload_data)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.put("/api/automations/{automation_id}", response_model=AutomationOut)
def update_automation(
    automation_id: int,
    payload: AutomationCreate,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> Automation:
    method = payload.http_method.upper()
    if method not in ALLOWED_HTTP_METHODS:
        raise HTTPException(status_code=400, detail=f"http_method not allowed: {method}")
    endpoint, _ = _validate_run_endpoint(payload.run_endpoint)
    entity = db.query(Automation).filter(Automation.id == automation_id, Automation.tenant_id == tenant_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Automation not found")
    payload_data = payload.model_dump()
    payload_data["http_method"] = method
    payload_data["run_endpoint"] = endpoint
    for key, value in payload_data.items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity


def _headers(target_host: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.getenv("WINDMILL_API_TOKEN")
    if token and target_host in TOKEN_TARGET_HOSTS:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.post("/api/automations/{automation_id}/run", response_model=ExecutionOut)
def run_automation(
    automation_id: int,
    payload: RunRequest,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> Execution:
    automation = db.query(Automation).filter(Automation.id == automation_id, Automation.tenant_id == tenant_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    _, target_host = _validate_run_endpoint(automation.run_endpoint)

    body: dict[str, object]
    try:
        body = json.loads(automation.payload_template or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload_template JSON: {exc}") from exc
    if payload.payload:
        body.update(payload.payload)

    start = time.perf_counter()
    code = None
    status = "error"
    response_body = ""
    try:
        response = requests.request(
            automation.http_method.upper(),
            automation.run_endpoint,
            headers=_headers(target_host),
            json=body,
            timeout=30,
        )
        code = response.status_code
        response_body = response.text[:5000]
        status = "success" if response.ok else "error"
    except Exception as exc:
        response_body = str(exc)
    elapsed = int((time.perf_counter() - start) * 1000)

    execution = Execution(
        tenant_id=tenant_id,
        client_id=automation.client_id,
        automation_id=automation.id,
        status=status,
        response_code=code,
        response_body=response_body,
        duration_ms=elapsed,
    )
    automation.last_run_at = datetime.now(timezone.utc)
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


@app.get("/api/executions", response_model=list[ExecutionOut])
def list_executions(
    client_id: int | None = None,
    limit: int = 100,
    _: str = Depends(require_user),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[Execution]:
    query = db.query(Execution).filter(Execution.tenant_id == tenant_id)
    if client_id is not None:
        query = query.filter(Execution.client_id == client_id)
    return query.order_by(Execution.created_at.desc()).limit(min(max(limit, 1), 500)).all()
