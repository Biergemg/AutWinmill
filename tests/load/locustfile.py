import os
import random
import string
import time
from locust import HttpUser, task, between, events

# Configuration
WM_WORKSPACE = os.getenv("WM_WORKSPACE", "demo")
WM_TOKEN = os.getenv("WM_TOKEN", "changeme")
WM_SCRIPT_PATH = os.getenv("WM_SCRIPT_PATH", "f/admin/einstein_kids/inbound_webhook")

class WindmillUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.client.headers.update({"Authorization": f"Bearer {WM_TOKEN}"})

    @task
    def execute_flow(self):
        # Generate random payload to avoid caching
        payload = {
            "payload": {
                "message": "".join(random.choices(string.ascii_letters, k=10)),
                "timestamp": time.time()
            },
            "signature": "test_signature"
        }
        
        # Endpoint for running a flow/script
        # Adjust path structure based on if it's a flow (f) or script (u)
        # The env var WM_SCRIPT_PATH should include the prefix (e.g. f/path or u/user/path)
        endpoint = f"/api/w/{WM_WORKSPACE}/jobs/run/{WM_SCRIPT_PATH}"
        
        with self.client.post(endpoint, json=payload, catch_response=True) as response:
            if response.status_code == 200 or response.status_code == 201:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}, Response: {response.text}")

# Hook for custom metrics or logging if needed
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting Load Test...")
