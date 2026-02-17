from typing import Any, Dict, Protocol, Optional

class WindmillPort(Protocol):
    """Puerto para interactuar con el entorno de Windmill"""
    
    def get_variable(self, path: str) -> Optional[str]:
        """Obtiene una variable de Windmill"""
        ...
        
    def get_resource(self, path: str) -> Dict[str, Any]:
        """Obtiene un recurso de Windmill"""
        ...
