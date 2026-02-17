import sys
import os

# Agregar src al path para que los tests puedan importar el paquete windmill_automation
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
