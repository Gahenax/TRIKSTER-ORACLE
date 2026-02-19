import pytest
from core.contract import RiskEvaluationResult, TailPercentiles
from pydantic import ValidationError

def test_contract_fuzzing_pls_bounds():
    """Verify PLS must be [0, 1]."""
    tp = TailPercentiles(p5=-0.5, p10=-0.3, p25=-0.1)
    
    # 1. Valid
    RiskEvaluationResult(
        pls=0.5, zone="GREEN", fragility=0.1, 
        tail_percentiles=tp, n_sims=100, 
        determinism_signature="a"*64, snapshot_id="s"
    )
    
    # 2. Invalid high
    with pytest.raises(ValidationError):
        RiskEvaluationResult(pls=1.01, zone="GREEN", fragility=0.1, tail_percentiles=tp, n_sims=1, determinism_signature="a"*64, snapshot_id="s")

    # 3. Invalid low
    with pytest.raises(ValidationError):
        RiskEvaluationResult(pls=-0.01, zone="GREEN", fragility=0.1, tail_percentiles=tp, n_sims=1, determinism_signature="a"*64, snapshot_id="s")

def test_contract_fuzzing_zone_enum():
    """Verify zone must be GREEN|YELLOW|RED."""
    tp = TailPercentiles(p5=0, p10=0, p25=0)
    with pytest.raises(ValidationError):
        RiskEvaluationResult(pls=0.5, zone="BLUE", fragility=0, tail_percentiles=tp, n_sims=1, determinism_signature="a"*64, snapshot_id="s")

def test_contract_signature_format():
    """Verify signature length and hex requirement."""
    tp = TailPercentiles(p5=0, p10=0, p25=0)
    # Short hash
    with pytest.raises(ValidationError):
         RiskEvaluationResult(pls=0.5, zone="RED", fragility=0, tail_percentiles=tp, n_sims=1, determinism_signature="abc", snapshot_id="s")
