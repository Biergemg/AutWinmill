from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from windmill_automation.infrastructure.database.base import Base


class LeadMixin:
    name: Mapped[str] = mapped_column(String, default="Unknown")
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_normalized: Mapped[str] = mapped_column(String, unique=True, index=True)
    avatar: Mapped[str] = mapped_column(String, default="mother")
    utm_source: Mapped[str | None] = mapped_column(String, nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String, nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String, nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String, nullable=True)
    landing_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LeadModel(LeadMixin, Base):
    __tablename__ = "ek_leads"
    
    lead_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
