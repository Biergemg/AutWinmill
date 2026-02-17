from typing import Any, Dict, Protocol, List, Optional
from dataclasses import dataclass

@dataclass
class AuditRecord:
    actor: str
    action: str
    details: Dict[str, Any]
    trace_id: Optional[str] = None
    workflow_id: Optional[str] = None
    event_id: Optional[str] = None

class PersistencePort(Protocol):
    """Puerto para operaciones de persistencia (Repository Pattern)"""
    
    def record_audit_log(self, record: AuditRecord) -> None:
        """Registra una entrada en el log de auditoría"""
        ...
    
    def get_audit_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera logs de auditoría recientes"""
        ...
