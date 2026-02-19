from typing import Dict, Any

def calculate_football_features(snapshot_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates numerical features for football simulation.
    Auditable proxies only.
    """
    # Example logic: rating diff, availability ratio, recent form proxy
    home_rating = snapshot_data.get("home_rating", 1500.0)
    away_rating = snapshot_data.get("away_rating", 1500.0)
    
    # Availability proxy: % of top 11 players available
    home_availability = snapshot_data.get("home_availability_ratio", 1.0)
    away_availability = snapshot_data.get("away_availability_ratio", 1.0)
    
    return {
        "rating_diff": home_rating - away_rating,
        "home_availability_impact": (1.0 - home_availability) * -100.0,
        "away_availability_impact": (1.0 - away_availability) * -100.0,
        "home_advantage": snapshot_data.get("home_advantage", 100.0)
    }
