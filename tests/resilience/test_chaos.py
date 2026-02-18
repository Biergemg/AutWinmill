import os
import requests
import time
import pytest

BASE_URL = os.getenv("WM_BASE_URL", "http://localhost:8000")
WORKSPACE = os.getenv("WM_WORKSPACE", "demo")
TOKEN = os.getenv("WM_TOKEN", "changeme")

@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {TOKEN}"})
    return s

def test_api_latency_degradation(client):
    """
    Check if API response time is within acceptable limits (resilience baseline).
    Failure here under load implies poor resilience.
    """
    start = time.time()
    resp = client.get(f"{BASE_URL}/api/w/{WORKSPACE}/jobs/list")
    latency = time.time() - start
    
    assert resp.status_code == 200
    assert latency < 2.0, f"API too slow: {latency}s"

def test_webhook_idempotency(client):
    """
    Simulate duplicate webhook delivery.
    Requires a flow that handles deduplication (e.g. by checking a signature or ID).
    """
    # This is a template test. In a real scenario, you'd target a specific flow endpoint
    # and assert that the second call returns "Already processed" or similar.
    webhook_path = os.getenv("WM_WEBHOOK_PATH", "f/admin/einstein_kids/inbound_webhook")
    url = f"{BASE_URL}/api/w/{WORKSPACE}/webhooks/{webhook_path}"
    
    unique_id = f"evt_{int(time.time())}"
    payload = {"id": unique_id, "data": "test"}
    
    # First call
    # resp1 = client.post(url, json=payload)
    # assert resp1.status_code == 200
    
    # Second call (duplicate)
    # resp2 = client.post(url, json=payload)
    # assert resp2.status_code == 200 # Should still be OK
    # assert "processed" not in resp2.text # Should verify it didn't trigger side effects twice
    
    pass
