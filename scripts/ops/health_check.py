import sys
import os
import json
import subprocess

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

from scripts.lib.json_logging import log_json

def check_postgres():
    """Verifica conectividad básica a Postgres vía Docker"""
    cmd = [
        "docker", "exec", "aut_windmill_postgres",
        "psql", "-U", "windmill", "-d", "windmill",
        "-c", "SELECT 1"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True, "OK"
    except subprocess.CalledProcessError:
        return False, "Connection refused or auth failed"
    except FileNotFoundError:
        return False, "Docker CLI not found"

def main():
    checks = {
        "postgres": check_postgres()
    }
    
    overall_status = "healthy"
    details = {}
    
    for service, (ok, msg) in checks.items():
        details[service] = {"status": "up" if ok else "down", "message": msg}
        if not ok:
            overall_status = "unhealthy"
    
    log_json(
        "info" if overall_status == "healthy" else "error",
        f"Health Check: {overall_status}",
        status=overall_status,
        extra=details
    )
    
    print(json.dumps({"status": overall_status, "details": details}))
    sys.exit(0 if overall_status == "healthy" else 1)

if __name__ == "__main__":
    main()
