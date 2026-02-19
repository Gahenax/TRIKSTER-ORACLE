"""
Simulation Engine V2 - Enhanced with full distribution output
Part of M1: SIM_ENGINE_V2_DISTRIBUTIONS milestone

CRITICAL ENHANCEMENTS:
- Returns DistributionObject instead of simplified dict
- Generates 3 scenarios (conservative, base, aggressive)
- Computes full statistical moments (mean, stdev, skew, kurtosis)
- Deterministic with seed
- Percentile monotonicity guaranteed
"""

import time
import numpy as np
import math
from typing import List
from scipy import stats

# Import distribution classes directly
from app.core.distribution import (
    DistributionObject,
    Scenario,
    PercentileSet,
    ScenarioParams,
    SCENARIO_DEFINITIONS,
    compute_percentiles,
    compute_distribution_stats
)
from app.core.spectral import analyze_mc_spectral_quality

def simulate_event_v2(
    event, 
    config
) -> DistributionObject:
    """
    Run Monte Carlo simulation V2 with full distribution output.
    
    Args:
        event: EventInput schema
        config: SimulationConfig schema
    
    Returns DistributionObject with:
    - Complete statistical moments
    - Percentiles (P5, P25, P50, P75, P95)
    - 3 scenarios (conservative, base, aggressive)
    - Reproducibility guarantee (deterministic seed)
    
    BACKWARDS COMPATIBILITY:
    - simulate_event() (V1) remains for existing endpoints
    - New endpoints use simulate_event_v2()
    """
    # Import here to avoid circular dependency
    from app.api.schemas import EventInput, SimulationConfig
    
    start_time = time.time()
    
    # Set seed for reproducibility
    if config.seed is not None:
        np.random.seed(config.seed)
    
    # Generate all 3 scenarios
    scenarios: List[Scenario] = []
    all_scenario_values = []
    
    for scenario_name in ["conservative", "base", "aggressive"]:
        scenario_params = SCENARIO_DEFINITIONS[scenario_name]
        scenario_result = _run_single_scenario(event, config, scenario_params)
        scenarios.append(scenario_result)
        
        # Collect values from base scenario for overall stats
        if scenario_name == "base":
            all_scenario_values = scenario_result.prob_home  # Store for stats
    
    # Compute overall distribution stats from BASE scenario
    # (We use base as the canonical scenario)
    base_scenario_idx = 1  # conservative(0), base(1), aggressive(2)
    base_scenario = scenarios[base_scenario_idx]
    
    # Re-run base to get raw distribution values for stats
    seed_adjusted = config.seed + 1000 if config.seed else None
    np.random.seed(seed_adjusted)
    
    raw_values = _generate_distribution_values(event, config, SCENARIO_DEFINITIONS["base"])
    
    # Next Level: Spectral Synchronization with Riemann Zeros
    from app.core.spectral import inject_zeta_entropy
    raw_values = inject_zeta_entropy(raw_values)
    
    # Compute statistical moments
    stats_dict = compute_distribution_stats(raw_values)
    percentiles_overall = compute_percentiles(raw_values)
    
    execution_time = (time.time() - start_time) * 1000
    # Spectral Calibration (New Improvement)
    spectral_report = analyze_mc_spectral_quality(raw_values)
    
    # Build complete DistributionObject
    distribution_obj = DistributionObject(
        sport=event.sport or "football",
        event_id=event.event_id,
        market="1X2",
        model_version="v2.0.0",
        n_sims=config.n_simulations,
        ci_level=0.95,  # Default CI level
        seed=config.seed,
        percentiles=percentiles_overall,
        mean=stats_dict["mean"],
        stdev=stats_dict["stdev"],
        skew=stats_dict["skew"],
        kurtosis=stats_dict["kurtosis"],
        scenarios=scenarios,
        notes=(
            f"Monte Carlo simulation with {config.n_simulations} iterations. "
            f"ELO-based logistic model. Home advantage: {event.home_advantage}. "
            f"Scenarios vary scale and variance to show range of outcomes. "
            f"Spectral Calibration: r-mean={spectral_report['r_mean']:.4f} ({spectral_report['spectral_regime']})"
        ),
        execution_time_ms=execution_time
    )
    
    return distribution_obj


def _generate_distribution_values(
    event,
    config,
    scenario_params: ScenarioParams
) -> np.ndarray:
    """
    Generate raw distribution values for a single scenario.
    
    Returns:
        np.ndarray of mapped values in [0, 1] range
    """
    # Constants
    SCALE_BASE = 400.0 / math.log(10.0)
    DRAW_BASE_PROB = 0.25
    
    # Apply scenario multiplier
    SCALE = SCALE_BASE * scenario_params.scale_multiplier
    
    threshold = -SCALE * math.log((1 - DRAW_BASE_PROB) / (1 + DRAW_BASE_PROB))
    
    # Expected rating difference
    expected_diff = event.home_rating + event.home_advantage - event.away_rating
    
    # Run simulations with scenario-adjusted variance
    scale_adjusted = SCALE * math.sqrt(scenario_params.variance_multiplier)
    simulated_diffs = np.random.logistic(
        loc=expected_diff, 
        scale=scale_adjusted, 
        size=config.n_simulations
    )
    
    # Map to [0,1] control values
    mapped_values = 1.0 / (1.0 + np.power(10.0, -simulated_diffs / 400.0))
    
    return mapped_values


def _run_single_scenario(
    event,
    config,
    scenario_params: ScenarioParams
) -> Scenario:
    """
    Execute a single scenario (conservative/base/aggressive).
    
    Returns:
        Scenario object with probabilities and percentiles
    """
    # Generate distribution
    mapped_values = _generate_distribution_values(event, config, scenario_params)
    
    # Constants for outcome classification
    SCALE_BASE = 400.0 / math.log(10.0)
    DRAW_BASE_PROB = 0.25
    SCALE = SCALE_BASE * scenario_params.scale_multiplier
    threshold = -SCALE * math.log((1 - DRAW_BASE_PROB) / (1 + DRAW_BASE_PROB))
    
    # Generate outcome classifications
    expected_diff = event.home_rating + event.home_advantage - event.away_rating
    scale_adjusted = SCALE * math.sqrt(scenario_params.variance_multiplier)
    simulated_diffs = np.random.logistic(
        loc=expected_diff,
        scale=scale_adjusted,
        size=config.n_simulations
    )
    
    home_wins = simulated_diffs > threshold
    away_wins = simulated_diffs < -threshold
    draws = ~(home_wins | away_wins)
    
    prob_home = float(np.mean(home_wins))
    prob_away = float(np.mean(away_wins))
    prob_draw = float(np.mean(draws))
    
    # Compute percentiles
    percentiles = compute_percentiles(mapped_values)
    
    # Build scenario
    scenario = Scenario(
        scenario_type=scenario_params.name,
        parameters={
            "scale_multiplier": scenario_params.scale_multiplier,
            "variance_multiplier": scenario_params.variance_multiplier
        },
        prob_home=prob_home,
        prob_draw=prob_draw,
        prob_away=prob_away,
        percentiles=percentiles,
        notes=scenario_params.notes
    )
    
    return scenario


# BACKWARDS COMPATIBLE V1 FUNCTION (for existing endpoints)
def simulate_event(event, config) -> dict:
    """
    LEGACY V1 simulation function.
    
    DEPRECATED: Use simulate_event_v2() for new code.
    This function remains for backwards compatibility only.
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
