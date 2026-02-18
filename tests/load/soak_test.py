import os
import subprocess
import sys

def run_soak_test():
    """
    Runs a soak test: moderate load for a long duration.
    """
    target_host = os.getenv("TARGET_HOST", "http://localhost:8000")
    users = int(os.getenv("SOAK_USERS", "20"))
    spawn_rate = int(os.getenv("SPAWN_RATE", "1"))
    # Default soak time 1 hour, but configurable
    run_time = os.getenv("SOAK_DURATION", "1h")
    
    print(f"Starting Soak Test against {target_host}")
    print(f"Users: {users}, Duration: {run_time}")

    # Use sys.executable to ensure we use the same python interpreter
    cmd = [
        sys.executable, "-m", "locust",
        "-f", "tests/load/locustfile.py",
        "--headless",
        "--host", target_host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--csv", "ops/benchmarks/results/soak_results"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Soak test completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Soak test failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    run_soak_test()
