from app.core.engine import simulate_event_v2
from app.api.schemas import EventInput, SimulationConfig
import json

def calibrate_jules():
    event = EventInput(
        event_id="test_calibration",
        sport="football",
        home_team="Team A",
        away_team="Team B",
        home_rating=1600,
        away_rating=1550,
        home_advantage=100
    )
    config = SimulationConfig(
        n_simulations=5000,
        seed=42
    )
    
    print("RUNNING JULES CALIBRATION (Spectral Chaos Audit)...")
    dist = simulate_event_v2(event, config)
    
    print(f"Result: {dist.notes}")
    
    # Extract r-mean from notes for a clean display
    import re
    r_mean_match = re.search(r"r-mean=([0-9\.]+)", dist.notes)
    if r_mean_match:
        print(f"SPECTRAL SIGNATURE (r-mean): {r_mean_match.group(1)}")
    
    # Check if meets GUE target
    r_val = float(r_mean_match.group(1)) if r_mean_match else 0.0
    if abs(r_val - 0.60) < 0.1:
        print("CALIBRATION SUCCESS: GUE Chaos detected.")
    else:
        print("CALIBRATION WARNING: Spectrum is Poisson/Ordered.")

if __name__ == "__main__":
    import sys
    import os
    # Add backend to path
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    calibrate_jules()
