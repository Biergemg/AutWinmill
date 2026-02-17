import json
import subprocess
import shlex
from typing import List, Dict, Any, Optional
from ..ports.persistence import PersistencePort, AuditRecord
from scripts.lib.json_logging import log_json

class DockerPostgresAdapter(PersistencePort):
    """
    Adaptador que interactúa con PostgreSQL a través de Docker CLI.
    Esta es una implementación de transición hasta tener un driver nativo configurado.
    """
    
    def __init__(self, container_name: str = "aut_windmill_postgres", db_user: str = "windmill", db_name: str = "windmill"):
        self.container_name = container_name
        self.db_user = db_user
        self.db_name = db_name

    def _run_psql_command(self, sql: str) -> str:
        """Ejecuta un comando SQL vía docker exec y retorna stdout"""
        cmd = [
            "docker", "exec", "-i", 
            self.container_name, 
            "psql", "-U", self.db_user, "-d", self.db_name,
            "-t", "-A",  # Tuples only, unaligned (easier parsing)
            "-c", sql
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            msg = f"Error ejecutando SQL en docker: {e.stderr}"
            log_json("error", msg, extra={"sql": sql, "exit_code": e.returncode})
            raise RuntimeError(msg)

    def record_audit_log(self, record: AuditRecord) -> None:
        # Serializar details a JSON
        details_json = json.dumps(record.details).replace("'", "''") # Simple SQL escape
        
        # Usamos la función record_platform_action si aplica, o insert directo
        # Aquí usaremos insert directo para ser genericos o la funcion existente record_platform_action
        
        # Construir query segura (relativamente, asumiendo inputs controlados por ahora)
        sql = f"""
        INSERT INTO audit_log (actor, action, details, trace_id, workflow_id, event_id)
        VALUES ('{record.actor}', '{record.action}', '{details_json}'::jsonb, 
                {f"'{record.trace_id}'" if record.trace_id else "NULL"},
                {f"'{record.workflow_id}'" if record.workflow_id else "NULL"},
                {f"'{record.event_id}'" if record.event_id else "NULL"}
        );
        """
        self._run_psql_command(sql)

    def get_audit_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Usamos json_agg para recuperar JSON directamente desde postgres
        sql = f"""
        SELECT json_agg(t) FROM (
            SELECT * FROM audit_log ORDER BY ts DESC LIMIT {limit}
        ) t;
        """
        output = self._run_psql_command(sql)
        if not output:
            return []
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return []
