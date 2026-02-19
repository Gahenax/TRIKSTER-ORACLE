import json
from typing import Dict, Any, List, Optional

class ChartBuilder:
    def __init__(self, policy_path: str):
        with open(policy_path, 'r') as f:
            self.policy = json.load(f)

    def build_chart(self, verdict: Dict[str, Any], sim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforces EXACTLY ONE chart policy. 
        Returns empty/disabled chart if verdict says no.
        """
        if not verdict.get("value_detected", False):
            return {
                "enabled": False,
                "type": "DENSITY",
                "data": {"series": []}
            }

        # Value detected -> Build the single chart
        series = sim_data.get("chart_series", {})
        
        return {
            "enabled": True,
            "type": "DENSITY",
            "data": {
                "x_label": "Probabilidad de Victoria",
                "y_label": "Densidad de Simulación",
                "series": [series]  # EXACTLY ONE series
            }
        }

def get_chart_builder():
    import os
    policy_path = os.path.join(os.path.dirname(__file__), "contracts", "chart_policy.json")
    return ChartBuilder(policy_path)
