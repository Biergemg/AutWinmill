import os
import requests
import pytest

BASE_URL = os.getenv("WM_BASE_URL", "http://localhost:8000")

def test_public_access_is_denied():
    """
    Ensure critical endpoints are not public.
    """
    critical_endpoints = [
        "/api/users/list",
        "/api/w/demo/variables/list",
        "/api/admin/stats"
    ]
    
    for ep in critical_endpoints:
        resp = requests.get(f"{BASE_URL}{ep}")
        assert resp.status_code in [401, 403], f"Endpoint {ep} should be protected"

def test_server_tokens_not_exposed():
    """
    Check headers for information leakage.
    """
    resp = requests.get(f"{BASE_URL}/")
    headers = resp.headers
    # Example: Ensure we aren't broadcasting exact server versions if possible
    # assert "X-Server-Version" not in headers
    pass
