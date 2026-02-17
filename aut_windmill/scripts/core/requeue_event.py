import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/core/requeue_event.py <dlq_id>")
        sys.exit(2)
    dlq_id = sys.argv[1]

    cmd = [
        "docker",
        "exec",
        "-i",
        "aut_windmill_postgres",
        "psql",
        "-U",
        os.getenv("POSTGRES_USER", "windmill"),
        "-d",
        os.getenv("POSTGRES_DB", "windmill"),
        "-v",
        f"dlq_id={dlq_id}",
        "-f",
        "/tmp/requeue_event.sql",
    ]

    subprocess.run(["docker", "cp", "scripts/core/requeue_event.sql", "aut_windmill_postgres:/tmp/requeue_event.sql"], check=False)
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
