import pytest
from features.football_features import calculate_football_features
from features.basketball_features import calculate_basketball_features
from features.mma_features import calculate_mma_features

def test_football_features_boundaries():
    # High difference
    res = calculate_football_features({"home_rating": 2500, "away_rating": 1200})
    assert res["rating_diff"] == 1300.0
    
    # Missing data - should be resilient or return defaults
    res2 = calculate_football_features({})
    assert "rating_diff" in res2
    assert res2["home_advantage"] == 100.0

def test_basketball_features_rest_days():
    # Extreme rest difference
    res = calculate_basketball_features({"home_rest_days": 10, "away_rest_days": 1})
    # rest_impact = (10-1) * 20.0 = 180.0
    assert res["rest_impact"] == 180.0

def test_mma_features_physical_delta():
    # Extreme reach diff
    res = calculate_mma_features({"fighterA_rating": 1500, "fighterB_rating": 1500, "reach_diff_cm": 10.0})
    assert res["reach_advantage"] == 50.0
    
    # Age penalty
    res2 = calculate_mma_features({"age_diff_years": 5.0})
    assert res2["age_decay_impact"] == -50.0
