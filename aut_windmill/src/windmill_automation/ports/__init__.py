from typing import Protocol, Any, Dict, Optional


class EventIngress(Protocol):
    def receive(self) -> Dict[str, Any]: ...


class Persistence(Protocol):
    def save_event(self, event: Dict[str, Any]) -> None: ...
    def update_status(self, event_id: str, status: str) -> None: ...


class Metrics(Protocol):
    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None: ...
