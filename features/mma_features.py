from typing import Dict, Any

def calculate_mma_features(snapshot_data: Dict[str, Any]) -> Dict[str, float]:
    """
    MMA numerical features.
    """
    fA_rating = snapshot_data.get("fighterA_rating", 1500.0)
    fB_rating = snapshot_data.get("fighterB_rating", 1500.0)
    
    # Reach/Stance/Age proxies
    reach_diff = snapshot_data.get("reach_diff_cm", 0.0)
    age_diff = snapshot_data.get("age_diff_years", 0.0)
    
    return {
        "rating_diff": fA_rating - fB_rating,
        "reach_advantage": reach_diff * 5.0,
        "age_decay_impact": age_diff * -10.0 # Older fighter penalty if diff is positive
    }
