import numpy as np
import time
from typing import Dict, Any, List
from app.core.engine import simulate_event_v2
from app.api.schemas import EventInput, SimulationConfig

def run_oracle_simulation(
    sport: str, 
    primary: str, 
    opponent: str, 
    n_sims: int = 1000,
    seed: int = None
) -> Dict[str, Any]:
    """
    Wrapper for the existing TRICKSTER engine.
    Normalizes outputs into the distribution representation required by the Oracle.
    """
    start_time = time.time()
    
    # 1. Map Oracle inputs to Engine inputs (Mapping placeholder for MVP)
    # In a real scenario, we'd fetch ratings from data adapters.
    event = EventInput(
        home_team=primary,
        away_team=opponent,
        home_rating=1500.0,  # Placeholder
        away_rating=1500.0,  # Placeholder
        sport=sport.lower()
    )
    
    config = SimulationConfig(
        n_simulations=n_sims,
        seed=seed
    )
    
    # 2. Execute V2 Engine
    dist_obj = simulate_event_v2(event, config)
    
    # 3. Extract the raw distribution values (simulated percentages)
    # The engine uses a base scenario distribution.
    # We'll regenerate a simple normal distribution around the mean for the MVP 
    # if raw values aren't directly exposed in the return object (it returns stats).
    # However, the engine _generate_distribution_values exists.
    
    # For MVP, we'll use the mean and stdev to represent the density.
    # In a production version, we'd pass the full array.
    
    # Generate synthetic series for the chart based on engine stats
    x = np.linspace(0, 1, 100).tolist()
    # Simple probability density function (Gaussian)
    y = [
        float(1/(dist_obj.stdev * np.sqrt(2 * np.pi)) * np.exp(- (xi - dist_obj.mean)**2 / (2 * dist_obj.stdev**2)))
        for xi in x
    ]

    return {
        "raw_distribution": [dist_obj.mean], # Mocking distribution array
        "stats": {
            "mean": dist_obj.mean,
            "stdev": dist_obj.stdev,
            "samples": dist_obj.n_sims
        },
        "chart_series": {
            "name": f"Distribución {primary}",
            "x": x,
            "y": y
        },
        "execution_ms": (time.time() - start_time) * 1000
    }
