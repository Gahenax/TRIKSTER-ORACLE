import pytest
from hypothesis import given, strategies as st, settings, Verbosity
from sim.engine import MonteCarloEngine, calculate_pls, get_risk_zone
from sim.scenario import Scenario

# Strategy for realistic but diverse features
features_strategy = st.fixed_dictionaries({
    "rating_diff": st.floats(min_value=-2000, max_value=2000),
    "home_advantage": st.floats(min_value=0, max_value=500),
    "home_availability_ratio": st.floats(min_value=0.5, max_value=1.0),
    "away_availability_ratio": st.floats(min_value=0.5, max_value=1.0)
})

@settings(max_examples=100, deadline=1000)
@given(
    features=features_strategy,
    stake=st.floats(min_value=1.0, max_value=1000000),
    profile=st.sampled_from(["CONSERVATIVE", "NEUTRAL", "RISKY"])
)
def test_sim_invariants_hypothesis(features, stake, profile):
    """
    Property-Based Testing for the Simulation Engine.
    Validates that regardless of inputs, the output contract is never violated.
    """
    engine = MonteCarloEngine(seed=42)
    outcomes = engine.run_simulation(features, n_sims=100)
    
    # Invariant 1: PLS is a probability [0, 1]
    pls = calculate_pls(outcomes)
    assert 0.0 <= pls <= 1.0
    
    # Invariant 2: Risk Zone is always valid
    zone = get_risk_zone(pls, profile)
    assert zone in ["GREEN", "YELLOW", "RED"]

    # Invariant 3: Outcomes are within physical bounds [-1, 1]
    for o in outcomes:
        assert -1.0 <= o <= 1.0

@given(
    features=features_strategy,
    seed=st.integers(min_value=0, max_value=2**32 - 1)
)
def test_signature_stability_property(features, seed):
    """Signature must be stable and valid for any input set."""
    engine = MonteCarloEngine(seed=seed)
    snap = {"data": "dummy"}
    sig = engine.generate_signature(snap, features, "NEUTRAL", 100.0)
    
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)

def test_engine_precision_upgrade_property():
    """Verify Sprint 8 adaptive logic: Non-Green must use more sims."""
    # Scenario designed to be risky (underdog home)
    risky_features = {"rating_diff": -300.0, "home_advantage": 50.0}
    sc = Scenario(
        event_key="test_prec",
        risk_profile="CONSERVATIVE", # Very sensitive
        stake=100.0,
        features=risky_features,
        snapshot_id="s1",
        snapshot_data={}
    )
    
    result = sc.evaluate() # n_sims is None => Adaptive
    
    if result["zone"] != "GREEN":
        assert result["n_sims"] == 10000
    else:
        # If it happens to be green, it could be 1000, 
        # but with these features it should be Red/Yellow.
        pass
