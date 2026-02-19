import os
import json
import pytest
import shutil
from core.exporter import ReportExporter, ExportGuardError
from sim.scenario import Scenario

@pytest.fixture
def exporter(tmp_path):
    return ReportExporter(export_root=str(tmp_path))

def test_report_export_schema_valid(exporter):
    # Mock result data from a scenario
    report_data = {
        "app_version": "1.0.0",
        "policy_version": "1.0.0-risk-only",
        "event_key": "ekey_test",
        "snapshot_id": "snap_1",
        "seed": 42,
        "config": {"n_sims": 100},
        "features_summary": {"rating_diff": 1.0},
        "results": {
            "pls_percent": 0.15,
            "zone": "YELLOW",
            "tail_percentiles": {"p5": -0.5},
            "fragility": 0.2
        },
        "audit": {
            "determinism_signature": "abc",
            "created_at_utc": "2026-01-01T00:00:00Z",
            "inputs_hashes": {"cfg": "hash1"}
        }
    }
    
    pack_dir = exporter.export_pack(report_data)
    assert os.path.exists(os.path.join(pack_dir, "report.json"))
    assert os.path.exists(os.path.join(pack_dir, "manifest.json"))
    assert os.path.exists(os.path.join(pack_dir, "hashes.json"))

def test_report_export_contains_audit_fields(exporter):
    report_data = {
        "app_version": "1.0.0", "policy_version": "1.0.0-risk-only", "event_key": "ekey_test",
        "snapshot_id": "snap_1", "seed": 42, "config": {}, "features_summary": {},
        "results": {"pls_percent": 0.1, "zone": "GREEN", "tail_percentiles": {}, "fragility": 0.0},
        "audit": {
            "determinism_signature": "audit_sig_123",
            "created_at_utc": "2026-01-01T00:00:00Z",
            "inputs_hashes": {"snapshot": "hash_a"}
        }
    }
    pack_dir = exporter.export_pack(report_data)
    with open(os.path.join(pack_dir, "report.json"), 'r') as f:
        data = json.load(f)
        assert "audit" in data
        assert data["audit"]["determinism_signature"] == "audit_sig_123"

def test_report_export_hashes_match_files(exporter):
    report_data = {
        "app_version": "1.0.0", "policy_version": "1.0.0-risk-only", "event_key": "x",
        "snapshot_id": "s", "seed": 0, "config": {}, "features_summary": {},
        "results": {"pls_percent": 0, "zone": "G", "tail_percentiles": {}, "fragility": 0},
        "audit": {"determinism_signature": "d", "created_at_utc": "t", "inputs_hashes": {}}
    }
    pack_dir = exporter.export_pack(report_data)
    with open(os.path.join(pack_dir, "hashes.json"), 'r') as f:
        hashes = json.load(f)
    
    # Manually verify report.json hash
    with open(os.path.join(pack_dir, "report.json"), 'rb') as f:
        import hashlib
        h = hashlib.sha256(f.read()).hexdigest()
        assert hashes["report.json"] == h

def test_report_export_prohibited_vocabulary_blocked(exporter):
    # Content with "bet" should be blocked
    bad_data = {
        "app_version": "1.0.0", "policy_version": "1.0.0", "event_key": "x",
        "snapshot_id": "s", "seed": 0, "config": {"note": "This is a good bet"}, 
        "features_summary": {},
        "results": {"pls_percent": 0, "zone": "G", "tail_percentiles": {}, "fragility": 0},
        "audit": {"determinism_signature": "d", "created_at_utc": "t", "inputs_hashes": {}}
    }
    with pytest.raises(ExportGuardError):
        exporter.export_pack(bad_data)

def test_report_export_is_deterministic_given_same_inputs(exporter, tmp_path):
    report_data = {
        "app_version": "1.0.0", "policy_version": "1.0.0", "event_key": "const",
        "snapshot_id": "s", "seed": 42, "config": {}, "features_summary": {},
        "results": {"pls_percent": 0, "zone": "G", "tail_percentiles": {}, "fragility": 0},
        "audit": {"determinism_signature": "d", "created_at_utc": "t", "inputs_hashes": {}}
    }
    # We want to check if the generated files are identical (ignoring timestamps in directory names if possible)
    # Actually, the task says "export is deterministic", usually referring to the simulation.
    # But for the export pack, if we pass the SAME report_data, we should get the SAME hashes.
    
    pack1 = exporter.export_pack(report_data)
    with open(os.path.join(pack1, "hashes.json"), 'r') as f:
        h1 = json.load(f)
        
    pack2 = exporter.export_pack(report_data)
    with open(os.path.join(pack2, "hashes.json"), 'r') as f:
        h2 = json.load(f)
        
    assert h1["report.json"] == h2["report.json"]
