"""
Tests for M2: UNCERTAINTY_LAYER_METRICS

Verification requirements:
1. Volatility score increases when variance increases
2. Data quality index decreases when key features missing
3. Confidence decay increases with older data timestamp
4. All metrics bounded to correct ranges
5. Edge cases handled (zero variance, missing data, etc)
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from app.core.uncertainty import (
    UncertaintyMetrics,
    compute_volatility_score,
    compute_data_quality_index,
    compute_confidence_decay,
    compute_all_uncertainty_metrics
)


# TEST 1: Volatility Score - Variance Relationship
def test_volatility_increases_with_variance():
    """
    M2 Test 1: Volatility score must increase when variance increases.
    
    Critical property: Higher spread = higher volatility score
    """
    # Low variance distribution (tight)
    np.random.seed(42)
    tight_dist = np.random.normal(loc=50, scale=5, size=1000)
    
    # High variance distribution (wide)
    wide_dist = np.random.normal(loc=50, scale=20, size=1000)
    
    tight_score = compute_volatility_score(tight_dist)
    wide_score = compute_volatility_score(wide_dist)
    
    # Wide distribution must have higher volatility
    assert wide_score > tight_score, \
        f"Wide dist volatility ({wide_score}) should be > tight dist ({tight_score})"
    
    # Check bounds
    assert 0 <= tight_score <= 100
    assert 0 <= wide_score <= 100
    
    # Approximate expected values
    assert tight_score < 40, "Tight distribution should have low volatility"
    assert wide_score > 50, "Wide distribution should have moderate-high volatility"
    
    print(f"TEST 1 PASSED: Tight={tight_score:.2f}, Wide={wide_score:.2f}")


def test_volatility_with_fat_tails():
    """
    M2 Test 1b: Volatility score detects fat-tailed distributions.
    """
    np.random.seed(123)
    
    # Normal distribution (thin tails)
    normal_dist = np.random.normal(loc=0, scale=1, size=10000)
    
    # Fat-tailed distribution (Student's t with df=3)
    from scipy.stats import t
    fat_tail_dist = t.rvs(df=3, loc=0, scale=1, size=10000, random_state=123)
    
    normal_score = compute_volatility_score(normal_dist)
    fat_tail_score = compute_volatility_score(fat_tail_dist)
    
    # Fat tails should have higher volatility (due to kurtosis)
    assert fat_tail_score >= normal_score, \
        "Fat-tailed distribution should have >= volatility"
    
    print(f"TEST 1b PASSED: Normal={normal_score:.2f}, Fat-tail={fat_tail_score:.2f}")


# TEST 2: Data Quality Index - Feature Coverage
def test_data_quality_decreases_with_missing_features():
    """
    M2 Test 2: Data quality must decrease when features are missing.
    
    Critical property: Missing features = lower quality score
    """
    # Complete features
    complete_features = {
        "home_rating": True,
        "away_rating": True,
        "home_form": True,
        "away_form": True,
        "head_to_head": True
    }
    
    # Partial features (missing 2)
    partial_features = {
        "home_rating": True,
        "away_rating": True,
        "home_form": False,  # Missing
        "away_form": False,  # Missing
        "head_to_head": True
    }
    
    complete_score = compute_data_quality_index(
        complete_features,
        data_age_days=1.0,
        sample_size=1000
    )
    
    partial_score = compute_data_quality_index(
        partial_features,
        data_age_days=1.0,
        sample_size=1000
    )
    
    # Complete features must have higher quality
    assert complete_score > partial_score, \
        f"Complete ({complete_score}) should be > partial ({partial_score})"
    
    # Check bounds
    assert 0 <= complete_score <= 100
    assert 0 <= partial_score <= 100
    
    # Approximate values
    assert complete_score >= 80, "Complete features should have high quality"
    assert partial_score < complete_score, "Missing features should reduce score"
    
    print(f"TEST 2 PASSED: Complete={complete_score:.2f}, Partial={partial_score:.2f}")


def test_data_quality_with_stale_data():
    """
    M2 Test 2b: Data quality decreases with data age.
    """
    features = {
        "feature_a": True,
        "feature_b": True,
        "feature_c": True
    }
    
    # Fresh data (1 day old)
    fresh_score = compute_data_quality_index(
        features,
        data_age_days=1.0,
        sample_size=1000
    )
    
    # Stale data (30 days old)
    stale_score = compute_data_quality_index(
        features,
        data_age_days=30.0,
        sample_size=1000
    )
    
    # Fresh should be better than stale
    assert fresh_score > stale_score, \
        f"Fresh ({fresh_score}) should be > stale ({stale_score})"
    
    print(f"TEST 2b PASSED: Fresh={fresh_score:.2f}, Stale={stale_score:.2f}")


# TEST 3: Confidence Decay - Data Age
def test_confidence_decay_increases_with_data_age():
    """
    M2 Test 3: Confidence decay must increase with older data.
    
    Critical property: Older data = faster confidence decay
    """
    # Fresh data
    fresh_decay = compute_confidence_decay(
        volatility_score=50.0,
        data_age_days=1.0,
        event_horizon_days=7.0
    )
    
    # Moderately old data
    moderate_decay = compute_confidence_decay(
        volatility_score=50.0,
        data_age_days=10.0,
        event_horizon_days=7.0
    )
    
    # Very stale data
    stale_decay = compute_confidence_decay(
        volatility_score=50.0,
        data_age_days=60.0,
        event_horizon_days=7.0
    )
    
    # Older data should decay faster
    assert moderate_decay > fresh_decay, \
        f"Moderate ({moderate_decay}) should be > fresh ({fresh_decay})"
    assert stale_decay > moderate_decay, \
        f"Stale ({stale_decay}) should be > moderate ({moderate_decay})"
    
    # Check bounds
    assert 0 <= fresh_decay <= 1
    assert 0 <= moderate_decay <= 1
    assert 0 <= stale_decay <= 1
    
    print(f"TEST 3 PASSED: Fresh={fresh_decay:.4f}, Moderate={moderate_decay:.4f}, Stale={stale_decay:.4f}")


def test_confidence_decay_with_volatility():
    """
    M2 Test 3b: Confidence decay increases with volatility.
    """
    # Low volatility
    low_vol_decay = compute_confidence_decay(
        volatility_score=20.0,
        data_age_days=5.0,
        event_horizon_days=7.0
    )
    
    # High volatility
    high_vol_decay = compute_confidence_decay(
        volatility_score=80.0,
        data_age_days=5.0,
        event_horizon_days=7.0
    )
    
    # High volatility should decay faster
    assert high_vol_decay > low_vol_decay, \
        "High volatility should cause faster decay"
    
    print(f"TEST 3b PASSED: Low-vol={low_vol_decay:.4f}, High-vol={high_vol_decay:.4f}")


# TEST 4: Edge Cases
def test_uncertainty_metrics_edge_cases():
    """
    M2 Test 4: Handle edge cases gracefully.
    """
    # Edge case 1: Zero variance (constant distribution)
    constant_dist = np.ones(1000)
    score = compute_volatility_score(constant_dist)
    assert 0 <= score <= 100, "Constant dist should give valid score"
    assert score < 10, "Constant dist should have very low volatility"
    
    # Edge case 2: No features
    empty_quality = compute_data_quality_index({})
    assert 0 <= empty_quality <= 100
    
    # Edge case 3: Negative data age (treat as fresh)
    decay = compute_confidence_decay(50.0, -5.0, 7.0)
    assert 0 <= decay <= 1
    
    # Edge case 4: Zero event horizon
    decay_zero_horizon = compute_confidence_decay(50.0, 5.0, 0.0)
    assert 0 <= decay_zero_horizon <= 1
    
    print("TEST 4 PASSED: Edge cases handled")


# TEST 5: Integration Test
def test_compute_all_uncertainty_metrics():
    """
    M2 Test 5: Integration test for all metrics together.
    """
    np.random.seed(456)
    dist = np.random.normal(loc=0.5, scale=0.15, size=1000)
    
    features = {
        "rating_home": True,
        "rating_away": True,
        "form": True,
        "injuries": False  # Missing
    }
    
    metrics = compute_all_uncertainty_metrics(
        distribution_values=dist,
        features_present=features,
        data_age_days=5.0,
        sample_size=500,
        event_horizon_days=10.0
    )
    
    # Type check
    assert isinstance(metrics, UncertaintyMetrics)
    
    # All fields present
    assert hasattr(metrics, 'volatility_score')
    assert hasattr(metrics, 'data_quality_index')
    assert hasattr(metrics, 'confidence_decay')
    assert hasattr(metrics, 'factors')
    assert hasattr(metrics, 'notes')
    
    # Bounds check
    assert 0 <= metrics.volatility_score <= 100
    assert 0 <= metrics.data_quality_index <= 100
    assert 0 <= metrics.confidence_decay <= 1
    
    # Factors populated
    assert 'distribution_cv' in metrics.factors
    assert 'data_age_days' in metrics.factors
    assert 'feature_coverage' in metrics.factors
    
    # Notes present
    assert isinstance(metrics.notes, str)
    assert len(metrics.notes) > 0
    
    print("TEST 5 PASSED: Integration test successful")
    print(f"  Volatility: {metrics.volatility_score:.2f}")
    print(f"  Data Quality: {metrics.data_quality_index:.2f}")
    print(f"  Confidence Decay: {metrics.confidence_decay:.4f}")
    print(f"  Notes: {metrics.notes}")


# TEST 6: Serialization
def test_uncertainty_metrics_serialization():
    """
    M2 Test 6: Verify Pydantic serialization works.
    """
    metrics = UncertaintyMetrics(
        volatility_score=75.5,
        data_quality_index=82.3,
        confidence_decay=0.12,
        factors={"test": 1.0},
        notes="Test notes"
    )
    
    # Serialize to dict
    data = metrics.model_dump()
    assert isinstance(data, dict)
    assert data['volatility_score'] == 75.5
    assert data['data_quality_index'] == 82.3
    assert data['confidence_decay'] == 0.12
    
    # Deserialize back
    metrics2 = UncertaintyMetrics(**data)
    assert metrics2.volatility_score == metrics.volatility_score
    
    print("TEST 6 PASSED: Serialization works")


# TEST 7: Synthetic Scenarios
def test_synthetic_scenarios():
    """
    M2 Test 7: Test realistic synthetic scenarios.
    """
    # Scenario A: High quality, low uncertainty
    np.random.seed(789)
    tight_dist = np.random.normal(0.5, 0.05, 1000)
    
    metrics_a = compute_all_uncertainty_metrics(
        distribution_values=tight_dist,
        features_present={"f1": True, "f2": True, "f3": True},
        data_age_days=1.0,
        sample_size=5000,
        event_horizon_days=7.0
    )
    
    # Should have low volatility, high quality, low decay
    assert metrics_a.volatility_score < 50, "Tight dist should have low volatility"
    assert metrics_a.data_quality_index > 70, "Complete features + fresh = high quality"
    assert metrics_a.confidence_decay < 0.15, "Good conditions = slow decay"
    
    # Scenario B: Low quality, high uncertainty
    wide_dist = np.random.normal(0.5, 0.25, 1000)
    
    metrics_b = compute_all_uncertainty_metrics(
        distribution_values=wide_dist,
        features_present={"f1": True, "f2": False, "f3": False},
        data_age_days=45.0,
        sample_size=100,
        event_horizon_days=2.0
    )
    
    # Should have high volatility, low quality, high decay
    assert metrics_b.volatility_score > metrics_a.volatility_score
    assert metrics_b.data_quality_index < metrics_a.data_quality_index
    assert metrics_b.confidence_decay > metrics_a.confidence_decay
    
    print("TEST 7 PASSED: Synthetic scenarios behave correctly")
    print(f"  Scenario A (good): vol={metrics_a.volatility_score:.1f}, qual={metrics_a.data_quality_index:.1f}")
    print(f"  Scenario B (poor): vol={metrics_b.volatility_score:.1f}, qual={metrics_b.data_quality_index:.1f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
