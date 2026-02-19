import pytest
from fastapi.testclient import TestClient
from web_viewer.app import app
import json

client = TestClient(app)

def test_viewer_landing():
    response = client.get("/")
    assert response.status_code == 200
    assert "Trickster Companion" in response.text

def test_viewer_rejects_invalid_json():
    response = client.post("/view", data={"report_json": "not-json"})
    assert "Invalid Report" in response.text

def test_viewer_rejects_invalid_schema():
    # Missing 'results'
    bad_data = {"event_key": "x", "audit": {}}
    response = client.post("/view", data={"report_json": json.dumps(bad_data)})
    assert "Invalid schema" in response.text

def test_viewer_renders_risk_only_fields():
    report_data = {
        "event_key": "test_ekey",
        "results": {
            "pls_percent": 0.12,
            "zone": "YELLOW",
            "tail_percentiles": {"p5": -0.6},
            "fragility": 0.5
        },
        "audit": {
            "determinism_signature": "sig_123",
            "created_at_utc": "2026-02-11T12:00:00Z"
        },
        "app_version": "1.0.0",
        "policy_version": "risk-v1",
        "snapshot_id": "snap-x"
    }
    response = client.post("/view", data={"report_json": json.dumps(report_data)})
    assert response.status_code == 200
    assert "12.0%" in response.text
    assert "sig_123" in response.text
    assert "ZONE YELLOW" in response.text

def test_viewer_legal_pages():
    for page in ["/privacy", "/terms", "/docs"]:
        response = client.get(page)
        assert response.status_code == 200
        assert "Trickster" in response.text
