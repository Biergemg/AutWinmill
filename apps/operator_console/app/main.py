from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta

import requests
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import create_token, require_user, verify_admin
from .db import Base, engine, get_db
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

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutWinmill Operator Console", version="0.1.0")
app.mount("/static", StaticFiles(directory="apps/operator_console/static"), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse("apps/operator_console/static/index.html")


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not verify_admin(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(payload.username))


@app.get("/api/summary", response_model=SummaryOut)
def summary(_: str = Depends(require_user), db: Session = Depends(get_db)) -> SummaryOut:
    since = datetime.utcnow() - timedelta(hours=24)
    executions_24h = db.query(func.count(Execution.id)).filter(Execution.created_at >= since).scalar() or 0
    success_24h = (
        db.query(func.count(Execution.id))
        .filter(Execution.created_at >= since, Execution.status == "success")
        .scalar()
        or 0
    )
    return SummaryOut(
        clients=db.query(func.count(Client.id)).scalar() or 0,
        automations=db.query(func.count(Automation.id)).scalar() or 0,
        executions_24h=executions_24h,
        success_24h=success_24h,
    )


@app.get("/api/clients", response_model=list[ClientOut])
def list_clients(_: str = Depends(require_user), db: Session = Depends(get_db)) -> list[Client]:
    return db.query(Client).order_by(Client.created_at.desc()).all()


@app.post("/api/clients", response_model=ClientOut)
def create_client(payload: ClientCreate, _: str = Depends(require_user), db: Session = Depends(get_db)) -> Client:
    exists = db.query(Client).filter(Client.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Client already exists")
    entity = Client(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.put("/api/clients/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    payload: ClientCreate,
    _: str = Depends(require_user),
    db: Session = Depends(get_db),
) -> Client:
    entity = db.query(Client).filter(Client.id == client_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in payload.model_dump().items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity


@app.get("/api/automations", response_model=list[AutomationOut])
def list_automations(_: str = Depends(require_user), db: Session = Depends(get_db)) -> list[Automation]:
    return db.query(Automation).order_by(Automation.created_at.desc()).all()


@app.post("/api/automations", response_model=AutomationOut)
def create_automation(
    payload: AutomationCreate,
    _: str = Depends(require_user),
    db: Session = Depends(get_db),
) -> Automation:
    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    entity = Automation(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.put("/api/automations/{automation_id}", response_model=AutomationOut)
def update_automation(
    automation_id: int,
    payload: AutomationCreate,
    _: str = Depends(require_user),
    db: Session = Depends(get_db),
) -> Automation:
    entity = db.query(Automation).filter(Automation.id == automation_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Automation not found")
    for key, value in payload.model_dump().items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.getenv("WINDMILL_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@app.post("/api/automations/{automation_id}/run", response_model=ExecutionOut)
def run_automation(
    automation_id: int,
    payload: RunRequest,
    _: str = Depends(require_user),
    db: Session = Depends(get_db),
) -> Execution:
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

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
            headers=_headers(),
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
        client_id=automation.client_id,
        automation_id=automation.id,
        status=status,
        response_code=code,
        response_body=response_body,
        duration_ms=elapsed,
    )
    automation.last_run_at = datetime.utcnow()
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


@app.get("/api/executions", response_model=list[ExecutionOut])
def list_executions(
    client_id: int | None = None,
    limit: int = 100,
    _: str = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[Execution]:
    query = db.query(Execution)
    if client_id is not None:
        query = query.filter(Execution.client_id == client_id)
    return query.order_by(Execution.created_at.desc()).limit(min(max(limit, 1), 500)).all()

