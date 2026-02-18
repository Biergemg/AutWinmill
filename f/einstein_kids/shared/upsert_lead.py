from __future__ import annotations

import logging
from typing import Any

from windmill_automation.application.services.lead_service import LeadService
from windmill_automation.domain.exceptions import DomainError
from windmill_automation.infrastructure.database.session import get_db_session
from windmill_automation.infrastructure.repositories.lead_repository import LeadRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _database_url_from_pg_resource(pg_resource: dict[str, Any] | None) -> str | None:
    if not pg_resource:
        return None
    host = pg_resource.get("host")
    user = pg_resource.get("user")
    password = pg_resource.get("password")
    dbname = pg_resource.get("dbname") or pg_resource.get("database")
    port = pg_resource.get("port", 5432)
    if not all([host, user, password, dbname]):
        return None
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


def main(lead_data: dict[str, Any], pg_resource: dict[str, Any] | None = None) -> dict[str, Any]:
    database_url = _database_url_from_pg_resource(pg_resource)
    db_gen = get_db_session(database_url=database_url)
    db = next(db_gen)

    try:
        repo = LeadRepository(db)
        service = LeadService(repo)
        result = service.process_lead(lead_data)
        logger.info("Lead processed successfully: %s", result)
        return {"success": True, "lead_id": result["lead_id"], "is_new": result["is_new"], "error": None}
    except DomainError as exc:
        logger.warning("Domain validation error: %s", exc)
        return {"success": False, "error": str(exc), "code": "VALIDATION_ERROR"}
    except Exception as exc:  # noqa: BLE001
        logger.error("Critical error processing lead", exc_info=True)
        return {"success": False, "error": str(exc)}
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
