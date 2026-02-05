import pytest
from app.core.risk import assess_risk
from app.api.schemas import RiskInfo

def test_risk_bands():
    # 1. Low Risk (Clear favorite)
    probs_low = {"home": 0.9, "draw": 0.05, "away": 0.05}
    bins = [i/20.0 for i in range(21)]
    freqs_low = [0]*19 + [100] # All in last bin
    dist_low = {"bins": bins, "frequencies": freqs_low}
    ci_low = {"95": {"lower": 0.95, "upper": 1.0}} # Narrow CI
    
    risk_low = assess_risk(probs_low, dist_low, {"95": ci_low["95"]})
    assert risk_low.band == "LOW"
    
    # 2. High Risk (Even match)
    probs_high = {"home": 0.333, "draw": 0.333, "away": 0.334}
    freqs_high = [5] * 20 # Uniform
    dist_high = {"bins": bins, "frequencies": freqs_high}
    ci_high = {"95": {"lower": 0.05, "upper": 0.95}} # Wide CI
    
    risk_high = assess_risk(probs_high, dist_high, {"95": ci_high["95"]})
    assert risk_high.band == "HIGH"

def test_balanced_probabilities_higher_risk():
    bins = [i/20.0 for i in range(21)]
    # Setup common dist/CI to isolate probability effect
    # Use a generic distribution for both
    freqs = [0]*10 + [100] + [0]*9 # Point mass in middle
    dist = {"bins": bins, "frequencies": freqs}
    ci = {"95": {"lower": 0.45, "upper": 0.55}}
    
    # Balanced (Uncertain)
    probs_balanced = {"home": 0.33, "draw": 0.33, "away": 0.34}
    risk_balanced = assess_risk(probs_balanced, dist, ci)
    
    # Unbalanced (Certain)
    probs_skewed = {"home": 0.8, "draw": 0.1, "away": 0.1}
    risk_skewed = assess_risk(probs_skewed, dist, ci)
    
    assert risk_balanced.score > risk_skewed.score

def test_risk_rationale_no_forbidden_terms():
    forbidden_terms = [
        "bet", "pick", "odd", "guaranteed", "sure", "profit", 
        "roi", "invest", "bankroll", "stake", "bookmaker"
    ]
    
    # Generate a risk object
    probs = {"home": 0.5, "draw": 0.5, "away": 0.0}
    bins = [i/20.0 for i in range(21)]
    freqs = [10] * 20
    dist = {"bins": bins, "frequencies": freqs}
    ci = {"95": {"lower": 0.0, "upper": 1.0}}
    
    risk = assess_risk(probs, dist, ci)
    rationale_lower = risk.rationale.lower()
    
    for term in forbidden_terms:
        assert term not in rationale_lower, f"Found forbidden term: {term}"
