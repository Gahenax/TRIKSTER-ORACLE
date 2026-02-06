import json
from fastapi.testclient import TestClient

# Adjust import to your actual app instance path.
from app.main import app

client = TestClient(app)

def _assert_error_contract(r, expected_status, expected_code, expected_path, expected_request_id):
    assert r.status_code == expected_status
    assert r.headers.get("content-type", "").startswith("application/json")
    data = r.json()
    assert data["error_code"] == expected_code
    assert data["path"] == expected_path
    assert data["request_id"] == expected_request_id
    assert "timestamp" in data

def test_404_contract_get():
    rid = "test-rid-404-get"
    r = client.get("/__does_not_exist__", headers={"X-Request-ID": rid})
    _assert_error_contract(r, 404, "not_found", "/__does_not_exist__", rid)

def test_404_contract_post():
    rid = "test-rid-404-post"
    r = client.post("/__does_not_exist__", headers={"X-Request-ID": rid})
    _assert_error_contract(r, 404, "not_found", "/__does_not_exist__", rid)

def test_405_contract():
    rid = "test-rid-405"
    # Assuming /health exists and is GET-only in your app
    r = client.post("/health", headers={"X-Request-ID": rid})
    _assert_error_contract(r, 405, "method_not_allowed", "/health", rid)

def test_422_contract_validation():
    rid = "test-rid-422"
    # This assumes /api/v1/simulate expects a body; sending empty should trigger 422.
    r = client.post("/api/v1/simulate", headers={"X-Request-ID": rid}, json={})
    assert r.status_code in (422, 400)
    # If 422, ensure contract:
    if r.status_code == 422:
        assert r.headers.get("content-type", "").startswith("application/json")
        data = r.json()
        assert data["error_code"] == "validation_error"
        assert data["path"] == "/api/v1/simulate"
        assert data["request_id"] == rid
