from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), default="default", nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    industry: Mapped[str] = mapped_column(String(120), default="general", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    owner: Mapped[str] = mapped_column(String(120), default="unassigned", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    automations: Mapped[list["Automation"]] = relationship("Automation", back_populates="client")


class Automation(Base):
    __tablename__ = "automations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), default="default", nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="mixed", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    run_endpoint: Mapped[str] = mapped_column(String(300), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), default="POST", nullable=False)
    payload_template: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="automations")
    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="automation")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(80), default="default", nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    automation_id: Mapped[int] = mapped_column(ForeignKey("automations.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    automation: Mapped[Automation] = relationship("Automation", back_populates="executions")
