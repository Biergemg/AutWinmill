import sys
import os
from pathlib import Path

import pytest

# Establecer entorno de pruebas por defecto para evitar fallos de importación en auth.py
os.environ.setdefault("OPERATOR_ENV", "test")
os.environ.setdefault("OPERATOR_JWT_SECRET", "test_secret_only")
os.environ.setdefault("OPERATOR_ADMIN_PASSWORD", "test_password_only")

# Agregar raiz y src al path para imports consistentes en local y CI
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Agregar src al path para que los tests puedan importar el paquete windmill_automation
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-integration", action="store_true", default=False, help="run integration tests")
    parser.addoption("--run-manual", action="store_true", default=False, help="run manual tests")
    parser.addoption("--run-load", action="store_true", default=False, help="run load tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_integration = config.getoption("--run-integration")
    run_manual = config.getoption("--run-manual")
    run_load = config.getoption("--run-load")

    skip_integration = pytest.mark.skip(reason="integration tests disabled (use --run-integration)")
    skip_manual = pytest.mark.skip(reason="manual tests disabled (use --run-manual)")
    skip_load = pytest.mark.skip(reason="load tests disabled (use --run-load)")

    for item in items:
        path = Path(str(item.fspath)).as_posix()
        if "/tests/manual/" in path and not run_manual:
            item.add_marker(skip_manual)
            continue
        if "/tests/load/" in path and not run_load:
            item.add_marker(skip_load)
            continue
        if any(segment in path for segment in ["/tests/multitenant/", "/tests/security/", "/tests/resilience/"]):
            if not run_integration:
                item.add_marker(skip_integration)
