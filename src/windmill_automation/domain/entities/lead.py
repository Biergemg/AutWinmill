from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Lead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(default="Unknown")
    email: EmailStr | None = None
    phone: str | None = None
    phone_normalized: str | None = None
    avatar: str = Field(default="mother")
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    landing_id: str | None = None
    event_start_at: datetime | None = None
