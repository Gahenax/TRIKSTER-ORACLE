import time
import numpy as np
import math
from app.api.schemas import EventInput, SimulationConfig

def simulate_event(event: EventInput, config: SimulationConfig) -> dict:
    """
    Run Monte Carlo simulation for a sports event.
    
    CRITICAL: Must be DETERMINISTIC.
    Same input + same seed → EXACT same output.
    
    Returns dict with:
    - prob_home, prob_draw, prob_away
    - distribution: {"bins": [...], "frequencies": [...]}
    - confidence_intervals: {"95": {"lower": ..., "upper": ...}, "99": {...}}
    - execution_time_ms
    """
    start_time = time.time()
    
    if config.seed is not None:
        np.random.seed(config.seed)
        
    # Constants
    SCALE = 400.0 / math.log(10.0)
    DRAW_BASE_PROB = 0.25
    threshold = -SCALE * math.log((1 - DRAW_BASE_PROB) / (1 + DRAW_BASE_PROB))
    
    # Expected rating difference
    expected_diff = event.home_rating + event.home_advantage - event.away_rating
    
    # Run simulations
    simulated_diffs = np.random.logistic(loc=expected_diff, scale=SCALE, size=config.n_simulations)
    
    # Determine outcomes
    home_wins = simulated_diffs > threshold
    away_wins = simulated_diffs < -threshold
    draws = ~(home_wins | away_wins)
    
    prob_home = float(np.mean(home_wins))
    prob_away = float(np.mean(away_wins))
    prob_draw = float(np.mean(draws))
    
    # Map to [0,1] control values
    mapped_values = 1.0 / (1.0 + np.power(10.0, -simulated_diffs / 400.0))
    
    # CIs
    ci_95 = np.percentile(mapped_values, [2.5, 97.5])
    ci_99 = np.percentile(mapped_values, [0.5, 99.5])
    
    # Distribution
    bins = np.linspace(0.0, 1.0, 21)
    hist, _ = np.histogram(mapped_values, bins=bins)
    
    execution_time = (time.time() - start_time) * 1000
    
    return {
        "prob_home": prob_home,
        "prob_draw": prob_draw,
        "prob_away": prob_away,
        "distribution": {
            "bins": bins.tolist(),
            "frequencies": hist.tolist()
        },
        "confidence_intervals": {
            "95": {"lower": float(ci_95[0]), "upper": float(ci_95[1])},
            "99": {"lower": float(ci_99[0]), "upper": float(ci_99[1])}
        },
        "execution_time_ms": execution_time
    }
