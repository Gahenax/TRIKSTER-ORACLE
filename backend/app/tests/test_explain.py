"""
Unit tests for explainability module (explain.py)
Tests T2.1 and T2.2 requirements from ROADMAP.py
"""

import pytest
from app.core.explain import (
    explain,
    generate_summary,
    generate_scenarios,
    generate_caveats,
    calculate_sensitivity,
    validate_text_compliance,
    FORBIDDEN_TERMS
)
from app.api.schemas import RiskInfo, ExplanationOutput


# Test fixtures
@pytest.fixture
def sample_probabilities():
    return {
        "prob_home": 0.55,
        "prob_draw": 0.25,
        "prob_away": 0.20
    }


@pytest.fixture
def sample_risk_low():
    return RiskInfo(
        score=25.0,
        band="LOW",
        rationale="Tight probability distribution with high confidence"
    )


@pytest.fixture
def sample_risk_high():
    return RiskInfo(
        score=75.0,
        band="HIGH",
        rationale="Wide distribution indicating significant uncertainty"
    )


@pytest.fixture
def sample_event_context():
    return {
        "home_team": "Barcelona",
        "away_team": "Real Madrid",
        "home_rating": 2100,
        "away_rating": 2050,
        "home_advantage": 100,
        "sport": "football"
    }


@pytest.fixture
def sample_simulation_result(sample_probabilities, sample_risk_low):
    return {
        "prob_home": sample_probabilities["prob_home"],
        "prob_draw": sample_probabilities["prob_draw"],
        "prob_away": sample_probabilities["prob_away"],
        "risk": sample_risk_low,
        "confidence_intervals": {
            "95": {"lower": 0.50, "upper": 0.60},
            "99": {"lower": 0.48, "upper": 0.62}
        },
        "model_version": "0.1.0",
        "config": {"n_simulations": 1000}
    }


class TestTerminologyCompliance:
    """Test T2.1 requirement: No forbidden gambling/certainty terms"""
    
    def test_validate_text_compliance_clean_text(self):
        """Clean analytical text should pass"""
        clean_text = (
            "The simulation estimates a probability of 55% based on the model. "
            "This analysis shows moderate uncertainty."
        )
        violations = validate_text_compliance(clean_text)
        assert len(violations) == 0, f"Clean text flagged violations: {violations}"
    
    def test_validate_text_compliance_forbidden_terms(self):
        """Text with forbidden terms should be detected"""
        forbidden_text = "This is a sure bet with guaranteed profit"
        violations = validate_text_compliance(forbidden_text)
        assert "bet" in violations
        assert "guaranteed" in violations
        assert "profit" in violations
    
    def test_forbidden_terms_coverage(self):
        """Ensure FORBIDDEN_TERMS list is comprehensive"""
        required_terms = ["bet", "pick", "odd", "guaranteed", "sure", "profit"]
        for term in required_terms:
            assert any(term in forbidden for forbidden in FORBIDDEN_TERMS), \
                f"Required forbidden term '{term}' not in FORBIDDEN_TERMS"
    
    def test_summary_no_forbidden_terms(
        self,
        sample_probabilities,
        sample_risk_low,
        sample_event_context
    ):
        """Generated summary must not contain forbidden terms"""
        summary = generate_summary(
            sample_probabilities,
            sample_risk_low,
            sample_event_context
        )
        violations = validate_text_compliance(summary)
        assert len(violations) == 0, \
            f"Summary contains forbidden terms: {violations}\nSummary: {summary}"
    
    def test_scenarios_no_forbidden_terms(
        self,
        sample_probabilities,
        sample_event_context
    ):
        """Generated scenarios must not contain forbidden terms"""
        scenarios = generate_scenarios(
            sample_probabilities,
            {"95": {"lower": 0.5, "upper": 0.6}},
            sample_event_context
        )
        all_text = " ".join([s.description for s in scenarios])
        violations = validate_text_compliance(all_text)
        assert len(violations) == 0, \
            f"Scenarios contain forbidden terms: {violations}"


class TestSummaryGeneration:
    """Test summary generation (T2.1)"""
    
    def test_summary_includes_probabilities(
        self,
        sample_probabilities,
        sample_risk_low,
        sample_event_context
    ):
        """Summary should mention key probabilities"""
        summary = generate_summary(
            sample_probabilities,
            sample_risk_low,
            sample_event_context
        )
        assert "55" in summary or "55.0" in summary, \
            "Summary should include home probability"
        assert "Barcelona" in summary or "Real Madrid" in summary, \
            "Summary should include team names"
    
    def test_summary_includes_risk_band(
        self,
        sample_probabilities,
        sample_risk_high,
        sample_event_context
    ):
        """Summary should mention risk assessment"""
        summary = generate_summary(
            sample_probabilities,
            sample_risk_high,
            sample_event_context
        )
        assert "HIGH" in summary or "75" in summary, \
            "Summary should reference high risk"
        assert "uncertainty" in summary.lower(), \
            "Summary should discuss uncertainty for high risk"
    
    def test_summary_includes_caveats(
        self,
        sample_probabilities,
        sample_risk_low,
        sample_event_context
    ):
        """Summary should include appropriate caveats"""
        summary = generate_summary(
            sample_probabilities,
            sample_risk_low,
            sample_event_context
        )
        caveat_keywords = ["estimate", "statistical", "not prediction", "model"]
        assert any(keyword in summary.lower() for keyword in caveat_keywords), \
            "Summary should include caveats about limitations"
    
    def test_summary_balanced_probabilities(
        self,
        sample_risk_low,
        sample_event_context
    ):
        """Summary for balanced probabilities should indicate competitiveness"""
        balanced_probs = {
            "prob_home": 0.35,
            "prob_draw": 0.33,
            "prob_away": 0.32
        }
        summary = generate_summary(
            balanced_probs,
            sample_risk_low,
            sample_event_context
        )
        competitive_keywords = ["balanced", "competitive", "close"]
        assert any(keyword in summary.lower() for keyword in competitive_keywords), \
            "Summary should indicate balanced/competitive nature"


class TestScenarioGeneration:
    """Test scenario generation (T2.1)"""
    
    def test_scenarios_include_most_probable(
        self,
        sample_probabilities,
        sample_event_context
    ):
        """Should generate a 'most probable' scenario"""
        scenarios = generate_scenarios(
            sample_probabilities,
            {"95": {"lower": 0.5, "upper": 0.6}},
            sample_event_context
        )
        scenario_names = [s.name for s in scenarios]
        assert any("probable" in name.lower() for name in scenario_names), \
            "Should include most probable scenario"
    
    def test_scenarios_include_surprise(
        self,
        sample_probabilities,
        sample_event_context
    ):
        """Should generate a 'surprise' scenario for unlikely outcome"""
        scenarios = generate_scenarios(
            sample_probabilities,
            {"95": {"lower": 0.5, "upper": 0.6}},
            sample_event_context
        )
        scenario_names = [s.name for s in scenarios]
        assert any("surprise" in name.lower() for name in scenario_names), \
            "Should include surprise/underdog scenario"
    
    def test_scenario_probabilities_valid(
        self,
        sample_probabilities,
        sample_event_context
    ):
        """Scenario probabilities should be valid (0-1 range)"""
        scenarios = generate_scenarios(
            sample_probabilities,
            {"95": {"lower": 0.5, "upper": 0.6}},
            sample_event_context
        )
        for scenario in scenarios:
            assert 0 <= scenario.probability <= 1, \
                f"Invalid probability {scenario.probability} for {scenario.name}"


class TestCaveatGeneration:
    """Test caveat generation (T2.1)"""
    
    def test_caveats_count(self):
        """Should generate multiple caveats"""
        caveats = generate_caveats("0.1.0", 1000, {})
        assert len(caveats) >= 3, \
            "Should generate at least 3 caveats"
    
    def test_caveats_mention_limitations(self):
        """Caveats should mention model limitations"""
        caveats = generate_caveats("0.1.0", 1000, {})
        all_caveats = " ".join(caveats).lower()
        limitation_keywords = [
            "limitation", "simplified", "does not account",
            "not forecast", "educational"
        ]
        assert any(keyword in all_caveats for keyword in limitation_keywords), \
            "Caveats should explicitly mention limitations"
    
    def test_caveats_no_forbidden_terms(self):
        """Caveats must not use forbidden gambling terms"""
        caveats = generate_caveats("0.1.0", 1000, {})
        all_text = " ".join(caveats)
        violations = validate_text_compliance(all_text)
        assert len(violations) == 0, \
            f"Caveats contain forbidden terms: {violations}"


class TestSensitivityAnalysis:
    """Test sensitivity analysis (T2.2)"""
    
    def test_sensitivity_returns_factors(self, sample_probabilities):
        """Should return list of sensitivity factors"""
        event_input = {
            "home_rating": 2100,
            "away_rating": 2050,
            "home_advantage": 100
        }
        factors = calculate_sensitivity(
            sample_probabilities,
            event_input,
            model_func=None  # Uses mock for now
        )
        assert isinstance(factors, list), "Should return list"
        assert len(factors) > 0, "Should return at least one factor"
    
    def test_sensitivity_factor_structure(self, sample_probabilities):
        """Each factor should have required fields"""
        event_input = {"home_rating": 2100, "away_rating": 2050}
        factors = calculate_sensitivity(sample_probabilities, event_input)
        
        for factor in factors:
            assert hasattr(factor, 'factor_name'), "Factor needs name"
            assert hasattr(factor, 'delta_probability'), "Factor needs delta"
            assert hasattr(factor, 'impact_level'), "Factor needs impact level"
    
    def test_sensitivity_impact_levels(self, sample_probabilities):
        """Impact levels should be LOW/MEDIUM/HIGH"""
        event_input = {"home_rating": 2100, "away_rating": 2050}
        factors = calculate_sensitivity(sample_probabilities, event_input)
        
        valid_levels = {"LOW", "MEDIUM", "HIGH"}
        for factor in factors:
            assert factor.impact_level in valid_levels, \
                f"Invalid impact level: {factor.impact_level}"
    
    def test_sensitivity_ordered_by_impact(self, sample_probabilities):
        """Factors should be ordered by impact (largest first)"""
        event_input = {"home_rating": 2100, "away_rating": 2050}
        factors = calculate_sensitivity(sample_probabilities, event_input)
        
        if len(factors) > 1:
            for i in range(len(factors) - 1):
                assert abs(factors[i].delta_probability) >= abs(factors[i+1].delta_probability), \
                    "Factors should be ordered by absolute impact"


class TestExplainIntegration:
    """Test complete explain() function (T2.1 + T2.2 integration)"""
    
    def test_explain_returns_valid_output(
        self,
        sample_simulation_result,
        sample_event_context
    ):
        """Should return properly structured ExplanationOutput"""
        explanation = explain(sample_simulation_result, sample_event_context)
        
        assert isinstance(explanation, ExplanationOutput)
        assert isinstance(explanation.summary, str)
        assert len(explanation.summary) > 50, "Summary should be substantial"
        assert isinstance(explanation.scenarios, list)
        assert len(explanation.scenarios) > 0, "Should have scenarios"
        assert isinstance(explanation.caveats, list)
        assert len(explanation.caveats) > 0, "Should have caveats"
    
    def test_explain_compliance_enforcement(
        self,
        sample_event_context
    ):
        """Should raise error if generated text violates terminology policy"""
        # This is a hypothetical test - in practice, our generators are compliant
        # But the function should validate and raise if violations occur
        
        # Mock result that might generate problematic text
        bad_result = {
            "prob_home": 0.99,  # Extreme probability
            "prob_draw": 0.005,
            "prob_away": 0.005,
            "risk": RiskInfo(score=5, band="LOW", rationale="This is a sure bet guaranteed!"),
            "confidence_intervals": {"95": {"lower": 0.98, "upper": 0.995}},
            "model_version": "0.1.0",
            "config": {"n_simulations": 1000}
        }
        
        # Note: Our current implementation is compliant, but this tests the validator
        # If we ever accidentally generate forbidden terms, it should be caught
        try:
            explanation = explain(bad_result, sample_event_context)
            # Validate manually since risk rationale has forbidden terms
            all_text = explanation.summary
            violations = validate_text_compliance(all_text)
            # We expect clean summary even with bad risk input
            assert len(violations) == 0
        except ValueError as e:
            # If it raises, that's also acceptable (strict mode)
            assert "forbidden" in str(e).lower()
    
    def test_explain_different_risk_levels(
        self,
        sample_simulation_result,
        sample_event_context,
        sample_risk_high
    ):
        """Explanation should adapt to different risk levels"""
        # Low risk
        result_low = sample_simulation_result.copy()
        explanation_low = explain(result_low, sample_event_context)
        
        # High risk
        result_high = sample_simulation_result.copy()
        result_high["risk"] = sample_risk_high
        explanation_high = explain(result_high, sample_event_context)
        
        # Summary should mention uncertainty differently
        assert "HIGH" in explanation_high.summary or "uncertainty" in explanation_high.summary.lower()
        assert explanation_low.summary != explanation_high.summary


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
