import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from sim.engine import MonteCarloEngine, calculate_pls, get_risk_zone

@dataclass
class Scenario:
    event_key: str
    risk_profile: str
    stake: float
    features: Dict[str, float]
    snapshot_id: str
    snapshot_data: Dict[str, Any]
    seed: int = 42
    
    def evaluate(self, n_sims: Optional[int] = None) -> Dict[str, Any]:
        """
        Evaluates the scenario.
        Sprint 8 Mutation: Adaptive n_sims.
        If n_sims is not provided, we use 1000 initially.
        If outcome is NOT Green, we upgrade to 10000 for precision.
        """
        engine = MonteCarloEngine(seed=self.seed)
        
        # Determine internal sims if not forced
        target_sims = n_sims if n_sims is not None else 1000
        
        def run_pass(count):
            outcomes = engine.run_simulation(self.features, n_sims=count)
            pls = calculate_pls(outcomes)
            zone = get_risk_zone(pls, self.risk_profile)
            return outcomes, pls, zone

        outcomes, pls, zone = run_pass(target_sims)
        
        # Adaptive Upgrade (Only if n_sims was not explicitly forced)
        if n_sims is None and zone != "GREEN":
            # RE-RUN with higher precision for higher risk zones
            target_sims = 10000
            outcomes, pls, zone = run_pass(target_sims)

        signature = engine.generate_signature(
            self.snapshot_data, 
            self.features, 
            self.risk_profile, 
            self.stake
        )
        
        tail_negative = [o for o in outcomes if o < 0]
        fragility = float(np.std(tail_negative)) if tail_negative else 0.0
        
        return {
            "pls": pls,
            "zone": zone,
            "fragility": fragility,
            "tail_percentiles": {
                "p5": float(np.percentile(outcomes, 5)),
                "p10": float(np.percentile(outcomes, 10)),
                "p25": float(np.percentile(outcomes, 25))
            },
            "n_sims": int(len(outcomes)),
            "determinism_signature": signature,
            "snapshot_id": self.snapshot_id
        }
