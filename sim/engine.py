import numpy as np
import random
import hashlib
import json
from typing import Dict, Any, List

class MonteCarloEngine:
    """
    Deterministic, reproducible simulation engine.
    Computes PLS (Probability of Large Loss).
    Large Loss = >= 30% of stake.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        # We don't use global random/np.random to avoid external state pollution
        # We use a local State instance or just re-seed before the loop

    def generate_signature(self, snapshot_data: Dict[str, Any], features: Dict[str, float], 
                           risk_profile: str, stake: float) -> str:
        """
        Creates a 'determinism signature' hash:
        H(snapshot_json + features_json + risk_profile + stake + seed)
        """
        data = {
            "snapshot": snapshot_data,
            "features": features,
            "risk_profile": risk_profile,
            "stake": stake,
            "seed": self.seed
        }
        dump = json.dumps(data, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest()

    def run_simulation(self, features: Dict[str, float], n_sims: int = 10000) -> List[float]:
        """
        Runs the simulation based on features.
        Deterministic: Re-seeds local generator.
        """
        # Local RNG for isolation
        rng = np.random.default_rng(self.seed)
        
        rating_diff = features.get("rating_diff", 0.0)
        home_advantage = features.get("home_advantage", 100.0)
        
        logit = (rating_diff + home_advantage) / 400.0
        p_win = 1.0 / (1.0 + np.exp(-logit))
        
        outcomes = []
        for _ in range(n_sims):
            is_win = rng.random() < p_win
            
            if is_win:
                gain = rng.normal(0.5, 0.2) # Adjusted for more realistic variance
            else:
                gain = rng.normal(-0.5, 0.3)
            
            outcomes.append(float(np.clip(gain, -1.0, 1.0)))
            
        return outcomes

def calculate_pls(outcomes: List[float]) -> float:
    """
    PLS (Probability of Large Loss)
    Large loss = >= 30% loss (outcome <= -0.3)
    """
    large_losses = [o for o in outcomes if o <= -0.3]
    return len(large_losses) / len(outcomes)

def get_risk_zone(pls: float, profile: str) -> str:
    """
    Determines Green/Yellow/Red zone based on profile thresholds.
    """
    if profile == "CONSERVATIVE":
        if pls < 0.08: return "GREEN"
        if pls < 0.15: return "YELLOW"
        return "RED"
    elif profile == "NEUTRAL":
        if pls < 0.10: return "GREEN"
        if pls < 0.20: return "YELLOW"
        return "RED"
    elif profile == "RISKY":
        if pls < 0.15: return "GREEN"
        if pls < 0.30: return "YELLOW"
        return "RED"
    return "UNKNOWN"
