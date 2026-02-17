import os
import json
from typing import Any, Dict, Optional
from ..ports.windmill import WindmillPort

class EnvWindmillAdapter(WindmillPort):
    """
    Adaptador que simula/obtiene valores del entorno.
    En Windmill real, muchas veces se usan librerías cliente, 
    pero también se pasan valores por ENV o argumentos.
    Este adaptador permite mockear fácilmente en tests.
    """
    
    def get_variable(self, path: str) -> Optional[str]:
        # En local/tests, buscamos en variables de entorno con prefijo WM_VAR_
        # Ejemplo: variable/foo -> WM_VAR_VARIABLE_FOO
        env_key = f"WM_VAR_{path.upper().replace('/', '_')}"
        return os.environ.get(env_key)
        
    def get_resource(self, path: str) -> Dict[str, Any]:
        # En local, simulamos recursos vía ENV con JSON
        env_key = f"WM_RES_{path.upper().replace('/', '_')}"
        val = os.environ.get(env_key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return {}
        return {}
