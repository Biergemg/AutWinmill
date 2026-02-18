import os
import subprocess
import sys
import time

def run_stress_test():
    """
    Runs a stress test using Locust, ramping up users until failure or timeout.
    """
    target_host = os.getenv("TARGET_HOST", "http://localhost:8000")
    users_step = int(os.getenv("USERS_STEP", "10"))
    max_users = int(os.getenv("MAX_USERS", "100"))
    spawn_rate = int(os.getenv("SPAWN_RATE", "5"))
    run_time = os.getenv("RUN_TIME", "1m")
    
    print(f"Starting Stress Test against {target_host}")
    print(f"Max Users: {max_users}, Step: {users_step}, Spawn Rate: {spawn_rate}")

    # Use sys.executable to ensure we use the same python interpreter
    cmd = [
        sys.executable, "-m", "locust",
        "-f", "tests/load/locustfile.py",
        "--headless",
        "--host", target_host,
        "--users", str(max_users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--csv", "ops/benchmarks/results/stress_results"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Stress test completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Stress test failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    run_stress_test()
