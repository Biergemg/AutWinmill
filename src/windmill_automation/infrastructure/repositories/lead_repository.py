from __future__ import annotations

from sqlalchemy import func, literal_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from windmill_automation.domain.entities.lead import Lead
from windmill_automation.infrastructure.database.models import LeadModel


class LeadRepository:
    def __init__(self, session: Session, model_class: type[LeadModel] = LeadModel):
        self.session = session
        self.model = model_class

    def upsert(self, lead_data: Lead) -> dict[str, object]:
        values = lead_data.model_dump(exclude_none=True)
        stmt = insert(self.model).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["phone_normalized"],
            set_={
                "name": stmt.excluded.name,
                "email": func.coalesce(self.model.email, stmt.excluded.email),
                "avatar": stmt.excluded.avatar,
                "updated_at": func.now(),
            },
        ).returning(self.model.lead_id, literal_column("xmax = 0").label("is_new"))

        result = self.session.execute(stmt).first()
        if result is None:
            raise RuntimeError("Lead upsert returned no row")
        self.session.commit()
        return {"lead_id": result.lead_id, "is_new": bool(result.is_new)}
