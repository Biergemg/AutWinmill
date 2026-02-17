import os
import sys
import subprocess
import glob
from typing import List, Tuple

def run_sql_test(file_path: str, db_config: dict) -> Tuple[bool, str]:
    """
    Ejecuta un script SQL de prueba usando docker exec psql.
    Se asume que el script SQL lanza un error (divide by zero, raise exception) si falla.
    """
    container = db_config.get("container", "aut_windmill_postgres")
    user = db_config.get("user", "windmill")
    db = db_config.get("db", "windmill")
    
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-U", user, "-d", db,
        "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"
    ]
    
    try:
        # Leemos el archivo y lo pasamos por stdin
        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        # Envolver en transacción por si acaso, aunque los scripts deberían manejarlo
        full_sql = "BEGIN;\n" + sql_content + "\nROLLBACK;"
        
        result = subprocess.run(
            cmd,
            input=full_sql,
            capture_output=True,
            text=True,
            check=True
        )
        return True, "OK"
    except subprocess.CalledProcessError as e:
        return False, f"FAILED: {e.stderr.strip()}"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

def main():
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "ops/db/tests"
    files = glob.glob(os.path.join(test_dir, "*.sql"))
    
    if not files:
        print(f"No SQL tests found in {test_dir}")
        sys.exit(0)
        
    print(f"Running {len(files)} SQL tests...")
    failures = []
    
    for f in files:
        print(f"Testing {os.path.basename(f)}...", end=" ", flush=True)
        ok, msg = run_sql_test(f, {})
        if ok:
            print("PASS")
        else:
            print("FAIL")
            print(f"  > {msg}")
            failures.append(f)
            
    if failures:
        print(f"\n{len(failures)} tests failed.")
        sys.exit(1)
    else:
        print("\nAll SQL tests passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
