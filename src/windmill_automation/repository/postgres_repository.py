from typing import Dict, Any

from src.windmill_automation.adapters.docker import DockerAdapter


class PostgresRepository:
    def __init__(self, adapter: DockerAdapter | None = None) -> None:
        self.adapter = adapter or DockerAdapter()

    def insert_event(self, event: Dict[str, Any]) -> bool:
        sql = (
            "INSERT INTO events(event_id, trace_id, payload, status) "
            f"VALUES ('{event['event_id']}', '{event['trace_id']}', '{event['payload']}', '{event['status']}');"
        )
        result = self.adapter.run_psql_command(sql)
        return result.returncode == 0

    def update_status(self, event_id: str, status: str) -> bool:
        sql = f"UPDATE events SET status = '{status}' WHERE event_id = '{event_id}';"
        result = self.adapter.run_psql_command(sql)
        return result.returncode == 0
