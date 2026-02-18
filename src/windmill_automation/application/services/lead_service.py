from __future__ import annotations

from typing import Any

from windmill_automation.domain.entities.lead import Lead
from windmill_automation.domain.exceptions import DomainError
from windmill_automation.ports.lead_repository import LeadRepositoryPort


class LeadService:
    def __init__(self, repository: LeadRepositoryPort):
        self.repository = repository

    def process_lead(self, lead_data: dict[str, Any]) -> dict[str, object]:
        normalized = dict(lead_data)
        if normalized.get("email") == "":
            normalized["email"] = None
        if not normalized.get("phone_normalized") and normalized.get("phone"):
            normalized["phone_normalized"] = normalized["phone"]

        try:
            lead = Lead(**normalized)
        except Exception as exc:  # noqa: BLE001
            raise DomainError(f"Validacion fallida: {exc}") from exc

        return self.repository.upsert(lead)
