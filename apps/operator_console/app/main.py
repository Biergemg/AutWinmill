import json
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, cast
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
import prometheus_client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint

from .auth import assert_secure_runtime, create_token, require_user, verify_admin
from .db import bootstrap_schema, close_engine, get_db
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


def _run_timeout_seconds() -> int:
    try:
        value = int(os.getenv("OPERATOR_RUN_TIMEOUT_SECONDS", "30"))
    except ValueError:
        value = 30
    return min(max(value, 3), 120)


def _http_pool_size() -> int:
    try:
        value = int(os.getenv("OPERATOR_HTTP_POOL_SIZE", "20"))
    except ValueError:
        value = 20
    return min(max(value, 5), 200)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=_http_pool_size(), pool_maxsize=_http_pool_size())
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    _.state.http_session = session
    try:
        yield
    finally:
        session.close()
        close_engine()


app = FastAPI(title="AutWinmill Operator Console", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
rate_limit_handler = cast(
    Callable[[Request, Exception], Response | Awaitable[Response]],
    _rate_limit_exceeded_handler,
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS
origins = [item.strip() for item in os.getenv("OPERATOR_ALLOWED_ORIGINS", "").split(",") if item.strip()]
if not origins:
    origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]
if not origins:
    origins = ["*"]
if os.getenv("OPERATOR_ENV", "dev").lower() in {"prod", "production"} and "*" in origins:
    raise RuntimeError("OPERATOR_ALLOWED_ORIGINS cannot be '*' in production")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=("*" not in origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Operator-Tenant"],
)

# Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# Metrics Endpoint
@app.get("/metrics")
def metrics() -> Response:
    return Response(prometheus_client.generate_latest(), media_type=prometheus_client.CONTENT_TYPE_LATEST)
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
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest) -> TokenResponse:
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
    request: Request,
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
        http_session = getattr(request.app.state, "http_session", requests)
        response = http_session.request(
            automation.http_method.upper(),
            automation.run_endpoint,
            headers=_headers(target_host),
            json=body,
            timeout=_run_timeout_seconds(),
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
