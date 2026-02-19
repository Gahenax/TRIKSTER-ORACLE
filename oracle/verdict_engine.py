import json
import numpy as np
from typing import Dict, List, Any, Optional

class VerdictEngine:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def analyze(self, distribution: List[float], mode: str, reference_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Implements deterministic verdict logic based on simulation distribution.
        """
        samples = len(distribution)
        min_samples = self.config[f"min_samples_{mode.lower()}"]
        
        value_detected = False
        value_strength = "NONE"
        confidence = "LOW"
        reason_codes = []
        kill_switches = []
        chart_enabled = False

        # 1. Sample Check
        if samples < min_samples:
            reason_codes.append("INSUFFICIENT_DATA")
            return self._compose_result(False, "NONE", "LOW", reason_codes, kill_switches, False)

        # 2. Distribution Metrics
        mean = np.mean(distribution)
        std = np.std(distribution)
        variance = np.var(distribution)
        # Simplified normalized variance for the purpose of the MVP
        norm_variance = std / mean if mean != 0 else 1.0 
        
        # 3. Multimodality (Simplified peak detection)
        hist, bins = np.histogram(distribution, bins=20)
        peaks = 0
        for i in range(1, len(hist)-1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                peaks += 1
        
        # 4. Edge Calculation
        edge = 0.0
        if reference_price:
            # Assume reference_price is implied probability if < 1.0, else decimal odds
            implied_prob = 1.0 / reference_price if reference_price > 1.0 else reference_price
            edge = mean - implied_prob
        else:
            # Baseline edge check (relative to 50% for binary scenarios if no ref)
            edge = abs(mean - 0.5)

        edge_min = self.config[f"edge_min_{mode.lower()}"]

        # 5. Rule Enforcement
        if edge < edge_min:
            reason_codes.append("NO_EDGE")
        
        if norm_variance > self.config["max_variance"]:
            reason_codes.append("HIGH_VARIANCE")
            
        if peaks > self.config["max_multimodality"]:
            reason_codes.append("MULTIMODAL_CHAOS")

        # 6. Final Verdict
        if not reason_codes:
            value_detected = True
            chart_enabled = True
            confidence = "HIGH" if mode == "ORACLE" else "MEDIUM"
            
            if edge > edge_min * 3:
                value_strength = "HIGH"
            elif edge > edge_min * 2:
                value_strength = "MEDIUM"
            else:
                value_strength = "LOW"
        else:
            value_detected = False
            chart_enabled = False
            value_strength = "NONE"
            confidence = "LOW"

        return self._compose_result(value_detected, value_strength, confidence, reason_codes, kill_switches, chart_enabled)

    def _compose_result(self, detected, strength, conf, reasons, kills, chart) -> Dict[str, Any]:
        return {
            "value_detected": detected,
            "value_strength": strength,
            "confidence": conf,
            "reason_codes": reasons,
            "kill_switches": kills,
            "chart_enabled": chart
        }

def get_engine():
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config", "verdict_defaults.json")
    return VerdictEngine(config_path)
