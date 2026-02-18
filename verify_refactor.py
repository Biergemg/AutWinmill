from __future__ import annotations

import os
import sys


def main() -> int:
    sys.path.insert(0, os.getcwd())
    try:
        from windmill_automation.config.settings import get_settings  # noqa: F401
        from windmill_automation.domain.entities.lead import Lead  # noqa: F401
        from windmill_automation.infrastructure.database.models import LeadModel  # noqa: F401
        from windmill_automation.infrastructure.repositories.lead_repository import LeadRepository  # noqa: F401
        from windmill_automation.application.services.lead_service import LeadService  # noqa: F401

        print("OK: refactor imports are coherent")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: refactor verification failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
