import pytest
import time
from app.core.engine import simulate_event
from app.api.schemas import EventInput, SimulationConfig

@pytest.fixture
def sample_event():
    return EventInput(
        event_id="test_1",
        home_team="Team A",
        away_team="Team B",
        home_rating=1500,
        away_rating=1500,
        home_advantage=0
    )

def test_engine_determinism(sample_event):
    config = SimulationConfig(n_simulations=1000, seed=42)
    result1 = simulate_event(sample_event, config)
    result2 = simulate_event(sample_event, config)
    
    # Check keys that should be identical
    assert result1["prob_home"] == result2["prob_home"]
    assert result1["distribution"]["frequencies"] == result2["distribution"]["frequencies"]
    assert result1["confidence_intervals"]["95"]["lower"] == result2["confidence_intervals"]["95"]["lower"]

def test_probabilities_sum_to_one(sample_event):
    config = SimulationConfig(n_simulations=1000, seed=1)
    result = simulate_event(sample_event, config)
    
    total = result["prob_home"] + result["prob_draw"] + result["prob_away"]
    assert abs(total - 1.0) < 0.001

def test_confidence_intervals(sample_event):
    config = SimulationConfig(n_simulations=1000, seed=1)
    result = simulate_event(sample_event, config)
    
    ci_95 = result["confidence_intervals"]["95"]
    ci_99 = result["confidence_intervals"]["99"]
    
    width_95 = ci_95["upper"] - ci_95["lower"]
    width_99 = ci_99["upper"] - ci_99["lower"]
    
    assert width_99 >= width_95
    assert ci_95["lower"] >= 0.0
    assert ci_95["upper"] <= 1.0

def test_execution_time_reasonable(sample_event):
    config = SimulationConfig(n_simulations=1000, seed=123)
    start = time.time()
    result = simulate_event(sample_event, config)
    duration = time.time() - start
    
    assert duration < 5.0 # Less than 5 seconds
    # Check that internal metric is also reasonable
    assert result["execution_time_ms"] < 5000

def test_n_sims_validation(sample_event):
    # Test valid sims
    config_min = SimulationConfig(n_simulations=100, seed=1)
    result_min = simulate_event(sample_event, config_min)
    assert result_min
    
    # Test invalid sims
    with pytest.raises(ValueError):
        SimulationConfig(n_simulations=10)
    with pytest.raises(ValueError):
        SimulationConfig(n_simulations=100000)
