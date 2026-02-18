from __future__ import annotations

from typing import Protocol

from windmill_automation.domain.entities.lead import Lead


class LeadRepositoryPort(Protocol):
    def upsert(self, lead_data: Lead) -> dict[str, object]:
        ...
