import os
import requests
import pytest
import uuid

# Configuration
BASE_URL = os.getenv("WM_BASE_URL", "http://localhost:8000")
TENANT_A = os.getenv("WM_TENANT_A", "workspace_a")
TOKEN_A = os.getenv("WM_TOKEN_A", "token_a")
TENANT_B = os.getenv("WM_TENANT_B", "workspace_b")
TOKEN_B = os.getenv("WM_TOKEN_B", "token_b")

@pytest.fixture
def client_a():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {TOKEN_A}"})
    return s

@pytest.fixture
def client_b():
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {TOKEN_B}"})
    return s

def test_tenant_isolation(client_a, client_b):
    """
    Verify that Tenant B cannot access a variable created by Tenant A.
    """
    var_name = f"isolation_test_{uuid.uuid4().hex}"
    var_value = "secret_data"
    
    # 1. Tenant A creates a secret/variable
    # Endpoint structure may vary, assuming standard Windmill API for variables
    create_url = f"{BASE_URL}/api/w/{TENANT_A}/variables/create"
    resp = client_a.post(create_url, json={"name": var_name, "value": var_value, "is_secret": False})
    
    # If API requires specific path or structure, we assume standard creation here.
    # Allow 200 or 201. If create fails, skip if it's due to permissions/env not set.
    if resp.status_code not in [200, 201]:
        pytest.skip(f"Could not create variable in Tenant A: {resp.text}")

    try:
        # 2. Tenant A can read it
        get_url_a = f"{BASE_URL}/api/w/{TENANT_A}/variables/get/{var_name}"
        resp_a = client_a.get(get_url_a)
        assert resp_a.status_code == 200, "Tenant A should see its own variable"
        assert resp_a.json()["value"] == var_value

        # 3. Tenant B tries to read it
        # Try accessing it via Tenant B's workspace context (if names are shared global)
        # OR try accessing Tenant A's endpoint with Tenant B's token (Cross-Tenant Access)
        
        # Scenario 1: Tenant B accessing Tenant A's endpoint
        get_url_cross = f"{BASE_URL}/api/w/{TENANT_A}/variables/get/{var_name}"
        resp_cross = client_b.get(get_url_cross)
        assert resp_cross.status_code in [403, 401], "Tenant B should not access Tenant A's endpoint"

        # Scenario 2: Tenant B checks if it exists in their workspace (namespace isolation)
        get_url_b = f"{BASE_URL}/api/w/{TENANT_B}/variables/get/{var_name}"
        resp_b = client_b.get(get_url_b)
        assert resp_b.status_code == 404, "Variable should not exist in Tenant B"

    finally:
        # Cleanup
        client_a.delete(f"{BASE_URL}/api/w/{TENANT_A}/variables/delete/{var_name}")
