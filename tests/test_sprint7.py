import pytest
import json
import os
from core.verify import verify_suite
from core.contract import RiskEvaluationResult

def test_baseline_suite_passes():
    """Verify that the baseline suite is consistent with the engine."""
    fixture_path = "tests/fixtures/baselines.json"
    assert verify_suite(fixture_path) is True

def test_output_contract_schema():
    """Verify that RiskEvaluationResult catches missing fields."""
    with pytest.raises(Exception):
        # Missing pls
        RiskEvaluationResult(zone="GREEN", fragility=0.1, n_sims=10, determinism_signature="x", snapshot_id="y")

def test_verify_runner_reports_failures(tmp_path):
    """Manually corrupt a local baseline and ensure it fails."""
    # 1. Create a dummy baseline
    base_file = tmp_path / "corrupt_base.json"
    dummy_data = [{
        "name": "Dummy",
        "inputs": {
            "event_key": "x", "risk_profile": "NEUTRAL", "stake": 10, 
            "features": {"rating_diff": 0, "home_advantage": 0}, 
            "snapshot_id": "y", "snapshot_data": {}
        },
        "expected_output": {
            "pls": 0.5, "zone": "NEUTRAL", "n_sims": 10, 
            "determinism_signature": "WRONG_SIGNATURE", "snapshot_id": "y"
        }
    }]
    with open(base_file, 'w') as f:
        json.dump(dummy_data, f)
    
    # 2. Run verification - should fail due to signature mismatch
    assert verify_suite(str(base_file)) is False
