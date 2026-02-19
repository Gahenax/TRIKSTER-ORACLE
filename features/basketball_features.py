from typing import Dict, Any

def calculate_basketball_features(snapshot_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Basketball numerical features.
    """
    home_rating = snapshot_data.get("home_rating", 1500.0)
    away_rating = snapshot_data.get("away_rating", 1500.0)
    
    # Rest days factor (back-to-back impact)
    home_rest_days = snapshot_data.get("home_rest_days", 2)
    away_rest_days = snapshot_data.get("away_rest_days", 2)
    
    rest_impact = (home_rest_days - away_rest_days) * 20.0
    
    return {
        "rating_diff": home_rating - away_rating,
        "rest_impact": rest_impact,
        "home_advantage": snapshot_data.get("home_advantage", 150.0)
    }
