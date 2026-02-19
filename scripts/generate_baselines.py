import json
import os
from sim.scenario import Scenario

def generate_baselines():
    targets = [
        {"name": "Strong Home Favorite", "rating_diff": 200.0, "ha": 100.0, "profile": "CONSERVATIVE"},
        {"name": "Weak Home Underdog", "rating_diff": -250.0, "ha": 50.0, "profile": "RISKY"},
        {"name": "Neutral Clash", "rating_diff": 0.0, "ha": 100.0, "profile": "NEUTRAL"},
        {"name": "Slight Away Favorite", "rating_diff": -50.0, "ha": 80.0, "profile": "NEUTRAL"},
    ]
    
    suite = []
    # Using 10k sims for baseline stability
    N_SIMS = 10000
    
    for t in targets:
        inputs = {
            "event_key": f"test_{t['name'].lower().replace(' ', '_')}",
            "risk_profile": t["profile"],
            "stake": 100.0,
            "features": {"rating_diff": t["rating_diff"], "home_advantage": t["ha"]},
            "snapshot_id": f"snap_{t['name'][:3].lower()}",
            "snapshot_data": {"meta": t["name"]}
        }
        
        sc = Scenario(**inputs)
        result = sc.evaluate(n_sims=N_SIMS)
        
        suite.append({
            "name": t["name"],
            "inputs": inputs,
            "expected_output": result
        })
        
    os.makedirs("tests/fixtures", exist_ok=True)
    with open("tests/fixtures/baselines.json", "w") as f:
        json.dump(suite, f, indent=2)
    print(f"Generated {len(suite)} baselines in tests/fixtures/baselines.json")

if __name__ == "__main__":
    generate_baselines()
