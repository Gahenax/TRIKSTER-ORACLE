import json
import time
import statistics
import sys
import os

# Add backend to path so imports work
sys.path.append(os.getcwd())

from app.core.engine import simulate_event
from app.core.risk import assess_risk
from app.api.schemas import EventInput, SimulationConfig

def load_samples():
    with open("app/data/sample_events.json", "r") as f:
        data = json.load(f)
    return [EventInput(**item) for item in data]

def run_demo():
    try:
        events = load_samples()
    except FileNotFoundError:
        print("Error: Could not find app/data/sample_events.json. Run from backend/ directory.")
        return

    target_event = events[0]
    
    print(f"--- Running Demo for Event: {target_event.home_team} vs {target_event.away_team} ---")
    
    # 1. Generate Example Output
    config = SimulationConfig(n_simulations=1000, seed=42)
    result = simulate_event(target_event, config)
    
    # Calculate Risk
    risk = assess_risk(
        probabilities={
            "home": result["prob_home"],
            "draw": result["prob_draw"],
            "away": result["prob_away"]
        },
        distribution_data=result["distribution"],
        confidence_intervals=result["confidence_intervals"]
    )
    
    # Combine for output
    output = result.copy()
    output["risk"] = risk.model_dump()
    
    print("\n--- JSON Output (Sample) ---")
    print(json.dumps(output, indent=2))
    
    # 2. Performance Metrics
    print("\n--- Performance Metrics ---")
    sim_counts = [100, 1000, 10000]
    
    for n in sim_counts:
        times = []
        for _ in range(5): # Run 5 times to get average
            config = SimulationConfig(n_simulations=n)
            res = simulate_event(target_event, config)
            times.append(res["execution_time_ms"])
        
        avg_time = statistics.mean(times)
        print(f"n={n}: {avg_time:.2f} ms")

if __name__ == "__main__":
    run_demo()
