from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry: str = Field(default="general", max_length=120)
    owner: str = Field(default="unassigned", max_length=120)
    status: str = Field(default="active", max_length=30)


class ClientOut(ClientCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AutomationCreate(BaseModel):
    client_id: int
    name: str = Field(min_length=2, max_length=120)
    channel: str = Field(default="mixed", max_length=50)
    status: str = Field(default="active", max_length=30)
    run_endpoint: str = Field(min_length=8, max_length=300)
    http_method: str = Field(default="POST", max_length=10)
    payload_template: str = Field(default="{}")


class AutomationOut(AutomationCreate):
    id: int
    created_at: datetime
    last_run_at: datetime | None = None

    class Config:
        from_attributes = True


class ExecutionOut(BaseModel):
    id: int
    client_id: int
    automation_id: int
    status: str
    response_code: int | None = None
    response_body: str
    duration_ms: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RunRequest(BaseModel):
    payload: dict[str, Any] | None = None


class SummaryOut(BaseModel):
    clients: int
    automations: int
    executions_24h: int
    success_24h: int

