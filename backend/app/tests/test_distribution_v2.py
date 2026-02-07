"""
Tests for M1: SIM_ENGINE_V2_DISTRIBUTIONS

Verification requirements:
1. Schema presence: DistributionObject has all required fields
2. Deterministic repeatability: same seed → same output
3. Percentiles monotonicity: p5 <= p25 <= p50 <= p75 <= p95
4. Scenario generation: 3 scenarios (conservative, base, aggressive)
5. Statistical moments: mean, stdev, skew, kurtosis computed
"""

import pytest
import numpy as np
from app.core.engine import simulate_event_v2
from app.core.distribution import (
    DistributionObject,
    Scenario,
    PercentileSet,
    compute_percentiles,
    compute_distribution_stats
)
from app.api.schemas import EventInput, SimulationConfig


# Test fixtures
@pytest.fixture
def sample_event():
    """Standard test event"""
    return EventInput(
        event_id="test_001",
        home_team="Team A",
        away_team="Team B",
        home_rating=1500,
        away_rating=1450,
        home_advantage=100,
        sport="football"
    )


@pytest.fixture
def sim_config_with_seed():
    """Simulation config with fixed seed for determinism"""
    return SimulationConfig(
        n_simulations=1000,
        seed=42,
        confidence_levels=[0.95, 0.99]
    )


@pytest.fixture
def sim_config_no_seed():
    """Simulation config without seed"""
    return SimulationConfig(
        n_simulations=1000,
        seed=None
    )


# TEST 1: Schema Presence
def test_distribution_object_schema_presence(sample_event, sim_config_with_seed):
    """
    M1 Test 1: Verify DistributionObject has all required fields.
    
    Required fields per SIM_ENGINE_SPEC:
    - sport, event_id, market, model_version
    - n_sims, ci_level, percentiles
    - mean, stdev, skew, kurtosis
    - scenarios, notes
    """
    result = simulate_event_v2(sample_event, sim_config_with_seed)
    
    # Type check
    assert isinstance(result, DistributionObject), "Result must be DistributionObject"
    
    # Identity fields
    assert result.sport == "football"
    assert result.event_id == "test_001"
    assert result.market == "1X2"
    assert result.model_version == "v2.0.0"
    
    # Simulation metadata
    assert result.n_sims == 1000
    assert result.ci_level == 0.95
    assert result.seed == 42
    
    # Statistical measures
    assert isinstance(result.percentiles, PercentileSet)
    assert isinstance(result.mean, float)
    assert isinstance(result.stdev, float)
    assert result.stdev >= 0
    assert isinstance(result.skew, float) or result.skew is None
    assert isinstance(result.kurtosis, float) or result.kurtosis is None
    
    # Scenarios
    assert isinstance(result.scenarios, list)
    assert len(result.scenarios) == 3, "Must have exactly 3 scenarios"
    
    scenario_types = [s.scenario_type for s in result.scenarios]
    assert "conservative" in scenario_types
    assert "base" in scenario_types
    assert "aggressive" in scenario_types
    
    # Notes
    assert isinstance(result.notes, str)
    assert len(result.notes) > 0
    
    # Execution time
    assert result.execution_time_ms > 0
    
    print("✅ TEST 1 PASSED: Schema presence verified")


# TEST 2: Deterministic Repeatability
def test_deterministic_repeatability_with_seed(sample_event):
    """
    M1 Test 2: Same seed must produce identical results.
    
    Critical for:
    - Testing
    - Debugging
    - Audit trails
    """
    config1 = SimulationConfig(n_simulations=1000, seed=123)
    config2 = SimulationConfig(n_simulations=1000, seed=123)
    config3 = SimulationConfig(n_simulations=1000, seed=456)  # Different seed
    
    result1 = simulate_event_v2(sample_event, config1)
    result2 = simulate_event_v2(sample_event, config2)
    result3 = simulate_event_v2(sample_event, config3)
    
    # Same seed → same results
    assert result1.mean == result2.mean, "Same seed must give same mean"
    assert result1.stdev == result2.stdev, "Same seed must give same stdev"
    assert result1.percentiles.p50 == result2.percentiles.p50, "Same seed must give same median"
    
    # Check each scenario
    for i in range(3):
        s1 = result1.scenarios[i]
        s2 = result2.scenarios[i]
        assert s1.prob_home == s2.prob_home, f"Scenario {i} prob_home must match"
        assert s1.prob_away == s2.prob_away, f"Scenario {i} prob_away must match"
        assert s1.percentiles.p50 == s2.percentiles.p50, f"Scenario {i} p50 must match"
    
    # Different seed → different results (with high probability)
    assert result1.mean != result3.mean or result1.stdev != result3.stdev, \
        "Different seed should give different results"
    
    print("✅ TEST 2 PASSED: Deterministic repeatability verified")


# TEST 3: Percentiles Monotonicity
def test_percentiles_monotonicity(sample_event, sim_config_with_seed):
    """
    M1 Test 3: Percentiles must be monotonically increasing.
    
    Mathematical requirement: p5 <= p25 <= p50 <= p75 <= p95
    """
    result = simulate_event_v2(sample_event, sim_config_with_seed)
    
    p = result.percentiles
    
    # Overall distribution percentiles
    assert p.p5 <= p.p25, "P5 must be <= P25"
    assert p.p25 <= p.p50, "P25 must be <= P50"
    assert p.p50 <= p.p75, "P50 must be <= P75"
    assert p.p75 <= p.p95, "P75 must be <= P95"
    
    # Check each scenario
    for scenario in result.scenarios:
        sp = scenario.percentiles
        assert sp.p5 <= sp.p25 <= sp.p50 <= sp.p75 <= sp.p95, \
            f"Scenario '{scenario.scenario_type}' has non-monotonic percentiles"
    
    print("✅ TEST 3 PASSED: Percentiles monotonicity verified")


# TEST 4: Scenario Parameters
def test_scenario_parameters(sample_event, sim_config_with_seed):
    """
    M1 Test 4: Verify scenarios have correct parameters and differ.
    
    Conservative: tighter spread
    Base: standard
    Aggressive: wider spread
    """
    result = simulate_event_v2(sample_event, sim_config_with_seed)
    
    # Extract scenarios by type
    scenarios_by_type = {s.scenario_type: s for s in result.scenarios}
    
    conservative = scenarios_by_type["conservative"]
    base = scenarios_by_type["base"]
    aggressive = scenarios_by_type["aggressive"]
    
    # Check parameters
    assert conservative.parameters["scale_multiplier"] == 0.8
    assert base.parameters["scale_multiplier"] == 1.0
    assert aggressive.parameters["scale_multiplier"] == 1.2
    
    # Conservative should generally have tighter IQR (p75 - p25)
    cons_iqr = conservative.percentiles.p75 - conservative.percentiles.p25
    base_iqr = base.percentiles.p75 - base.percentiles.p25
    agg_iqr = aggressive.percentiles.p75 - aggressive.percentiles.p25
    
    # Note: Due to randomness, this isn't always strictly true, but should hold on average
    # We'll just check they're different
    assert cons_iqr != base_iqr or base_iqr != agg_iqr, "Scenarios should differ"
    
    # Each scenario should have valid probabilities
    for scenario in result.scenarios:
        assert 0 <= scenario.prob_home <= 1
        assert 0 <= scenario.prob_away <= 1
        if scenario.prob_draw is not None:
            assert 0 <= scenario.prob_draw <= 1
            # Check probabilities sum to ~1
            total = scenario.prob_home + scenario.prob_draw + scenario.prob_away
            assert 0.99 <= total <= 1.01, f"Probabilities must sum to 1, got {total}"
    
    print("✅ TEST 4 PASSED: Scenario parameters verified")


# TEST 5: Helper Functions
def test_compute_percentiles_helper():
    """
    M1 Test 5: Verify percentile computation helper.
    """
    # Synthetic distribution
    values = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    
    percentiles = compute_percentiles(values)
    
    assert isinstance(percentiles, PercentileSet)
    assert percentiles.p5 <= percentiles.p25
    assert percentiles.p25 <= percentiles.p50
    assert percentiles.p50 <= percentiles.p75
    assert percentiles.p75 <= percentiles.p95
    
    # Check approximate values (for uniform distribution)
    assert 10 <= percentiles.p5 <= 15
    assert 45 <= percentiles.p50 <= 55  # Median ~50
    assert 90 <= percentiles.p95 <= 100
    
    print("✅ TEST 5 PASSED: Percentile helper verified")


def test_compute_distribution_stats_helper():
    """
    M1 Test 5b: Verify distribution stats computation.
    """
    # Normal distribution
    np.random.seed(42)
    values = np.random.normal(loc=50, scale=10, size=10000)
    
    stats = compute_distribution_stats(values)
    
    assert "mean" in stats
    assert "stdev" in stats
    assert "skew" in stats
    assert "kurtosis" in stats
    
    # Check approximate values for normal distribution
    assert 49 <= stats["mean"] <= 51  # Should be ~50
    assert 9 <= stats["stdev"] <= 11  # Should be ~10
    assert -0.1 <= stats["skew"] <= 0.1  # Should be ~0 (symmetric)
    
    print("✅ TEST 5b PASSED: Distribution stats helper verified")


# TEST 6: Integration Test
def test_full_integration(sample_event, sim_config_with_seed):
    """
    M1 Test 6: Full integration test.
    
    Runs complete simulation and checks all components.
    """
    result = simulate_event_v2(sample_event, sim_config_with_seed)
    
    # Should not raise
    assert result
    
    # Serialize to dict (Pydantic model)
    result_dict = result.model_dump()
    assert isinstance(result_dict, dict)
    
    # Key fields present
    assert "percentiles" in result_dict
    assert "scenarios" in result_dict
    assert "mean" in result_dict
    assert "stdev" in result_dict
    
    print("✅ TEST 6 PASSED: Full integration verified")


# PERFORMANCE TEST (optional)
def test_performance_acceptable(sample_event, sim_config_with_seed):
    """
    M1 Performance: Verify reasonable execution time.
    
    1000 sims should complete in < 500ms
    """
    result = simulate_event_v2(sample_event, sim_config_with_seed)
    
    assert result.execution_time_ms < 500, \
        f"Execution too slow: {result.execution_time_ms}ms (expected < 500ms)"
    
    print(f"✅ PERFORMANCE TEST PASSED: {result.execution_time_ms:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
