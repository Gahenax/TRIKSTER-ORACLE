"""
Explainability Module - Generate human-readable interpretations
TRICKSTER-ORACLE Educational Analytics Platform

This module transforms technical simulation outputs into narratives that:
- Are educational and analytical (never promotional or gambling-focused)
- Include appropriate caveats and limitations
- Use only permitted terminology (see GLOSSARY.md)
- Help users understand probability, risk, and uncertainty
"""

from typing import Dict, List, Optional
from app.api.schemas import (
    ExplanationOutput,
    ScenarioInfo,
    SensitivityFactor,
    RiskInfo
)


# Forbidden terms from GLOSSARY.md
FORBIDDEN_TERMS = {
    "bet", "pick", "odd", "line", "spread", "parlay", "bookmaker",
    "stake", "bankroll", "unit", "sharp", "lock", "sure bet",
    "guaranteed", "certain", "certainty", "foolproof", "will win",
    "can't lose", "profit", "sure thing", "investment"
}


def validate_text_compliance(text: str) -> List[str]:
    """
    Check if text contains forbidden gambling/certainty terms.
    
    Args:
        text: Text to validate
        
    Returns:
        List of forbidden terms found (empty if compliant)
    """
    text_lower = text.lower()
    found_terms = []
    
    for term in FORBIDDEN_TERMS:
        if term in text_lower:
            found_terms.append(term)
    
    return found_terms


def generate_summary(
    probabilities: Dict[str, float],
    risk: RiskInfo,
    event_context: Dict
) -> str:
    """
    Generate executive summary (3-4 lines) of the simulation results.
    
    Args:
        probabilities: {prob_home, prob_draw, prob_away}
        risk: Risk assessment info
        event_context: Event metadata (teams, ratings, etc.)
        
    Returns:
        Human-readable summary paragraph
    """
    home_team = event_context.get("home_team", "Home Team")
    away_team = event_context.get("away_team", "Away Team")
    
    prob_home = probabilities.get("prob_home", 0) * 100
    prob_away = probabilities.get("prob_away", 0) * 100
    prob_draw = probabilities.get("prob_draw", 0) * 100
    
    # Determine most likely outcome
    outcomes = [
        ("home", prob_home, home_team),
        ("away", prob_away, away_team),
        ("draw", prob_draw, "Draw")
    ]
    most_likely = max(outcomes, key=lambda x: x[1])
    
    # Build summary with caveats
    summary_parts = []
    
    # Main probability statement
    if most_likely[1] > 50:
        summary_parts.append(
            f"The simulation estimates a {most_likely[1]:.1f}% probability that "
            f"{most_likely[2]} will be the outcome, based on the provided ratings and model parameters."
        )
    else:
        summary_parts.append(
            f"The simulation shows relatively balanced probabilities: "
            f"{home_team} ({prob_home:.1f}%), Draw ({prob_draw:.1f}%), {away_team} ({prob_away:.1f}%). "
            f"This suggests a highly competitive scenario."
        )
    
    # Risk context
    risk_context = {
        "LOW": "with high confidence and narrow uncertainty range",
        "MEDIUM": "with moderate uncertainty",
        "HIGH": "with significant uncertainty and wide confidence intervals"
    }
    summary_parts.append(
        f"The risk assessment is {risk.band} ({risk.score:.0f}/100), "
        f"{risk_context.get(risk.band, 'with typical uncertainty')}."
    )
    
    # Caveat
    summary_parts.append(
        "These are statistical estimates based on limited historical data and "
        "a simplified model—not predictions of the actual outcome."
    )
    
    return " ".join(summary_parts)


def generate_scenarios(
    probabilities: Dict[str, float],
    confidence_intervals: Dict[str, Dict[str, float]],
    event_context: Dict
) -> List[ScenarioInfo]:
    """
    Generate key scenarios: most likely outcome and surprise scenario.
    
    Args:
        probabilities: Outcome probabilities
        confidence_intervals: CI ranges
        event_context: Event metadata
        
    Returns:
        List of ScenarioInfo objects
    """
    home_team = event_context.get("home_team", "Home Team")
    away_team = event_context.get("away_team", "Away Team")
    
    prob_home = probabilities.get("prob_home", 0)
    prob_away = probabilities.get("prob_away", 0)
    prob_draw = probabilities.get("prob_draw", 0)
    
    scenarios = []
    
    # Most probable scenario
    outcomes = [
        ("Home Win", prob_home, home_team),
        ("Away Win", prob_away, away_team),
        ("Draw", prob_draw, "Draw")
    ]
    most_likely = max(outcomes, key=lambda x: x[1])
    
    scenarios.append(ScenarioInfo(
        name="Most Probable Outcome",
        probability=most_likely[1],
        description=(
            f"{most_likely[0]} is the most likely result according to the model, "
            f"with an estimated probability of {most_likely[1]*100:.1f}%. "
            f"This is based on the rating differential and home advantage parameters."
        )
    ))
    
    # Surprise/underdog scenario
    least_likely = min(outcomes, key=lambda x: x[1])
    if least_likely[1] > 0.05:  # Only if non-negligible
        scenarios.append(ScenarioInfo(
            name="Surprise Scenario",
            probability=least_likely[1],
            description=(
                f"{least_likely[0]} has the lowest estimated probability ({least_likely[1]*100:.1f}%), "
                f"but remains a plausible outcome. Unexpected factors not captured by the model "
                f"could shift this scenario's likelihood."
            )
        ))
    
    # Competitive scenario (if probabilities are close)
    max_prob = max(prob_home, prob_away, prob_draw)
    if max_prob < 0.5:  # No clear favorite
        scenarios.append(ScenarioInfo(
            name="Highly Competitive",
            probability=1.0 - max_prob,
            description=(
                f"With no outcome exceeding 50% probability, this event is highly competitive. "
                f"Small changes in form, tactics, or external factors could significantly "
                f"influence the result."
            )
        ))
    
    return scenarios


def generate_caveats(
    model_version: str,
    n_simulations: int,
    event_context: Dict
) -> List[str]:
    """
    Generate limitations and caveats for the analysis.
    
    Args:
        model_version: Model version string
        n_simulations: Number of simulations performed
        event_context: Event metadata
        
    Returns:
        List of caveat strings
    """
    caveats = [
        "This analysis uses a simplified ELO-based model and does not account for "
        "injuries, team news, weather conditions, tactical changes, or motivation factors.",
        
        f"The simulation is based on {n_simulations:,} Monte Carlo iterations. "
        f"While this provides statistical robustness, the underlying model (v{model_version}) "
        f"has inherent limitations and assumptions.",
        
        "Probabilities represent the model's estimate given the input parameters, "
        "not a forecast of what will actually happen. Real-world events are influenced "
        "by countless variables beyond this model's scope.",
        
        "Historical ratings may not reflect current team form, recent transfers, "
        "or other dynamic factors. Use this analysis as one input among many, "
        "not as a definitive assessment.",
        
        "This is an educational tool for understanding probability and risk analysis. "
        "It is not designed for, and should not be used for, gambling or betting decisions."
    ]
    
    return caveats


def calculate_sensitivity(
    base_probabilities: Dict[str, float],
    event_input: Dict,
    model_func: callable = None
) -> List[SensitivityFactor]:
    """
    Perform lightweight sensitivity analysis (what-if scenarios).
    
    Tests how changes in key variables affect probabilities.
    
    Args:
        base_probabilities: Baseline probabilities
        event_input: Original event parameters
        model_func: Function to recalculate probabilities (from model.py)
        
    Returns:
        List of SensitivityFactor objects, ordered by impact
    """
    if model_func is None:
        # Placeholder: will be replaced when model.py is available
        # For now, return mock sensitivity data
        return _mock_sensitivity(base_probabilities, event_input)
    
    sensitivity_factors = []
    base_prob_home = base_probabilities.get("prob_home", 0)
    
    # Test 1: Increase home advantage by 50
    modified_input = event_input.copy()
    modified_input["home_advantage"] = event_input.get("home_advantage", 100) + 50
    new_probs = model_func(**modified_input)
    delta_home_adv = (new_probs["prob_home"] - base_prob_home) * 100
    
    sensitivity_factors.append(SensitivityFactor(
        factor_name="Home Advantage (+50 points)",
        delta_probability=round(delta_home_adv, 2),
        impact_level="HIGH" if abs(delta_home_adv) > 5 else 
                     "MEDIUM" if abs(delta_home_adv) > 2 else "LOW"
    ))
    
    # Test 2: Improve home team rating by 50 points
    modified_input = event_input.copy()
    modified_input["home_rating"] = event_input.get("home_rating", 1500) + 50
    new_probs = model_func(**modified_input)
    delta_rating = (new_probs["prob_home"] - base_prob_home) * 100
    
    sensitivity_factors.append(SensitivityFactor(
        factor_name="Home Team Rating (+50 ELO)",
        delta_probability=round(delta_rating, 2),
        impact_level="HIGH" if abs(delta_rating) > 5 else 
                     "MEDIUM" if abs(delta_rating) > 2 else "LOW"
    ))
    
    # Sort by absolute impact
    sensitivity_factors.sort(key=lambda x: abs(x.delta_probability), reverse=True)
    
    return sensitivity_factors[:3]  # Return top 3 factors


def _mock_sensitivity(base_probs: Dict, event_input: Dict) -> List[SensitivityFactor]:
    """Mock sensitivity data for testing before model.py is available."""
    return [
        SensitivityFactor(
            factor_name="Home Advantage (+50 points)",
            delta_probability=3.2,
            impact_level="MEDIUM"
        ),
        SensitivityFactor(
            factor_name="Home Team Rating (+50 ELO)",
            delta_probability=4.8,
            impact_level="MEDIUM"
        ),
        SensitivityFactor(
            factor_name="Recent Form Adjustment",
            delta_probability=2.1,
            impact_level="LOW"
        ),
    ]


def explain(
    simulation_result: Dict,
    event_context: Dict,
    model_func: callable = None
) -> ExplanationOutput:
    """
    Main explanation generator. Transforms technical output into user-friendly narrative.
    
    Args:
        simulation_result: Dict with probabilities, CI, distribution, risk
        event_context: Event metadata (teams, ratings, etc.)
        model_func: Optional model function for sensitivity analysis
        
    Returns:
        ExplanationOutput with summary, scenarios, caveats, sensitivity
        
    Raises:
        ValueError: If generated text contains forbidden terms
    """
    probabilities = {
        "prob_home": simulation_result.get("prob_home", 0),
        "prob_away": simulation_result.get("prob_away", 0),
        "prob_draw": simulation_result.get("prob_draw", 0),
    }
    
    risk = simulation_result.get("risk")
    confidence_intervals = simulation_result.get("confidence_intervals", {})
    model_version = simulation_result.get("model_version", "0.1.0")
    n_sims = simulation_result.get("config", {}).get("n_simulations", 1000)
    
    # Generate components
    summary = generate_summary(probabilities, risk, event_context)
    scenarios = generate_scenarios(probabilities, confidence_intervals, event_context)
    caveats = generate_caveats(model_version, n_sims, event_context)
    
    # Sensitivity analysis (optional, depends on model availability)
    sensitivity = None
    if model_func:
        event_input = {
            "home_rating": event_context.get("home_rating"),
            "away_rating": event_context.get("away_rating"),
            "home_advantage": event_context.get("home_advantage", 100)
        }
        sensitivity = calculate_sensitivity(probabilities, event_input, model_func)
    
    # Create explanation output
    explanation = ExplanationOutput(
        summary=summary,
        scenarios=scenarios,
        caveats=caveats,
        sensitivity=sensitivity
    )
    
    # Validate compliance with anti-gambling terminology
    all_text = summary + " ".join([s.description for s in scenarios])
    violations = validate_text_compliance(all_text)
    if violations:
        raise ValueError(
            f"Generated explanation contains forbidden terms: {violations}. "
            f"This violates the project's anti-gambling policy (see GLOSSARY.md)."
        )
    
    return explanation
