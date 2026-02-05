import math
from app.api.schemas import RiskInfo

def assess_risk(
    probabilities: dict[str, float],
    distribution_data: dict,
    confidence_intervals: dict
) -> RiskInfo:
    """
    Calculate risk score (0-100) and band (LOW/MEDIUM/HIGH).
    
    Returns RiskInfo with:
    - score: float (0-100)
    - band: str ("LOW" | "MEDIUM" | "HIGH")
    - rationale: str (human-readable explanation)
    """
    # 1. Entropy (Outcomes)
    probs = [p for p in probabilities.values() if p > 0]
    if not probs:
        entropy = 0.0
    else:
        entropy = -sum(p * math.log(p) for p in probs)
    max_entropy = math.log(3)
    entropy_score = (entropy / max_entropy) * 100
    
    # 2. Variance (Distribution)
    bins = distribution_data["bins"]
    freqs = distribution_data["frequencies"]
    total_count = sum(freqs)
    
    if total_count == 0:
        std_dev = 0.0
    else:
        bin_centers = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
        weighted_sum = sum(c * f for c, f in zip(bin_centers, freqs))
        mean = weighted_sum / total_count
        weighted_sq_diff = sum(((c - mean)**2) * f for c, f in zip(bin_centers, freqs))
        variance = weighted_sq_diff / total_count
        std_dev = math.sqrt(variance)
        
    max_std = 0.2887 # Uniform dist
    std_score = min(100.0, (std_dev / max_std) * 100)
    
    # 3. CI Width (95%)
    ci_95 = confidence_intervals.get("95", {"upper": 1.0, "lower": 0.0})
    # Handle dict or list if previous implementation left artifacts, 
    # but strictly following new signature it should be dict with upper/lower
    width = ci_95["upper"] - ci_95["lower"]
    width_score = width * 100 # 0-100 directly
    
    # Combined Score (Weighted)
    # Entropy: 40%, Std: 30%, CI Width: 30%
    final_score = 0.4 * entropy_score + 0.3 * std_score + 0.3 * width_score
    final_score = min(100.0, max(0.0, final_score))
    
    # Banding
    if final_score < 33:
        band = "LOW"
    elif final_score < 67:
        band = "MEDIUM"
    else:
        band = "HIGH"
        
    # Rationale
    if band == "LOW":
        rationale = (
            f"Low uncertainty detected (Risk Score: {final_score:.1f}). "
            "The model estimates a distinct outcome pattern with high statistical confidence."
        )
    elif band == "MEDIUM":
        rationale = (
            f"Moderate uncertainty (Risk Score: {final_score:.1f}). "
            "Analysis shows a likely outcome but with significant variance in simulation results."
        )
    else:
        rationale = (
            f"High uncertainty (Risk Score: {final_score:.1f}). "
            "The probability distribution is wide, indicating multiple plausible scenarios."
        )
        
    return RiskInfo(
        score=final_score,
        band=band,
        rationale=rationale
    )
