import sys
import os

# Establecer entorno de pruebas por defecto para evitar fallos de importación en auth.py
os.environ.setdefault("OPERATOR_ENV", "test")
os.environ.setdefault("OPERATOR_JWT_SECRET", "test_secret_only")
os.environ.setdefault("OPERATOR_ADMIN_PASSWORD", "test_password_only")

# Agregar src al path para que los tests puedan importar el paquete windmill_automation
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
