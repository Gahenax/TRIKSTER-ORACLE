from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app, compute_signature_sha256

@pytest.fixture()
def tmp_reports_dir(tmp_path: Path, monkeypatch):
    d = tmp_path / "exports"
    d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("REPORTS_DIR", str(d))
    return d

def make_report(report_id: str, payload: dict) -> dict:
    sig = compute_signature_sha256(payload)
    return {
        "report_id": report_id,
        "created_at": "2026-02-11T00:00:00Z",
        "payload": payload,
        "signature_sha256": sig,
    }

def test_health_ok(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_read_only_methods_blocked(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    client = TestClient(app)
    assert client.post("/api/reports").status_code == 405
    assert client.put("/api/reports/x").status_code == 405
    assert client.delete("/api/reports/x").status_code == 405

def test_report_api_roundtrip_and_verify(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    payload = {"a": 1, "b": {"c": 2}}
    rep = make_report("r1", payload)
    (tmp_reports_dir / "r1.json").write_text(json.dumps(rep), encoding="utf-8")

    client = TestClient(app)
    r = client.get("/api/reports/r1")
    assert r.status_code == 200
    assert r.json()["payload"] == payload

    v = client.get("/api/reports/r1/verify")
    assert v.status_code == 200
    assert v.json()["ok"] is True

def test_report_html_view(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    payload = {"pls_percent": 0.1, "results": {"zone": "GREEN", "pls_percent": 0.1, "tail_percentiles": {}, "fragility": 0}, "audit": {"determinism_signature": "x", "created_at_utc": "t"}, "event_key": "ekey"}
    rep = make_report("r1", payload)
    # The template expects specific keys in payload
    (tmp_reports_dir / "r1.json").write_text(json.dumps(rep), encoding="utf-8")
    
    client = TestClient(app)
    r = client.get("/reports/r1")
    assert r.status_code == 200
    assert "Risk Evaluation Report" in r.text

def test_signature_mismatch_rejected(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    payload = {"x": 9}
    rep = make_report("r2", payload)
    rep["signature_sha256"] = "0" * 64
    (tmp_reports_dir / "r2.json").write_text(json.dumps(rep), encoding="utf-8")

    client = TestClient(app)
    r = client.get("/api/reports/r2")
    assert r.status_code == 400
    assert "signature" in r.json()["detail"]

def test_invalid_report_format_422(tmp_reports_dir, monkeypatch):
    monkeypatch.setenv("VIEWER_API_KEY", "")
    (tmp_reports_dir / "bad.json").write_text("{not json", encoding="utf-8")
    client = TestClient(app)
    r = client.get("/api/reports/bad")
    assert r.status_code in (404, 422)
