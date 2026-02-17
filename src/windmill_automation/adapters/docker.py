import os
import subprocess
from typing import List, Optional


class DockerAdapter:
    def __init__(self, container_name: str = "aut_windmill_postgres") -> None:
        self.container_name = container_name

    def cp_to_container(self, src_path: str, dst_path: str) -> bool:
        result = subprocess.run(["docker", "cp", src_path, f"{self.container_name}:{dst_path}"], capture_output=True, text=True)
        return result.returncode == 0

    def run_psql_file(self, sql_path_in_container: str, vars: Optional[List[str]] = None) -> subprocess.CompletedProcess:
        cmd = [
            "docker",
            "exec",
            "-i",
            self.container_name,
            "psql",
            "-U",
            os.getenv("POSTGRES_USER", "windmill"),
            "-d",
            os.getenv("POSTGRES_DB", "windmill"),
            "-f",
            sql_path_in_container,
        ]
        if vars:
            for v in vars:
                cmd.extend(["-v", v])
        return subprocess.run(cmd, capture_output=True, text=True)

    def run_psql_command(self, sql_command: str) -> subprocess.CompletedProcess:
        cmd = [
            "docker",
            "exec",
            "-i",
            self.container_name,
            "psql",
            "-U",
            os.getenv("POSTGRES_USER", "windmill"),
            "-d",
            os.getenv("POSTGRES_DB", "windmill"),
            "-c",
            sql_command,
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
