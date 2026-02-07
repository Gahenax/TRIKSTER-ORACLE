"""
Uncertainty Metrics Module - M2: UNCERTAINTY_LAYER_METRICS

Provides quantitative measures of prediction uncertainty:
1. Volatility Score (0-100): Distribution spread and variance
2. Data Quality Index (0-100): Feature coverage and recency
3. Confidence Decay (0-1): Temporal degradation of prediction confidence

These metrics enable users to understand:
- How reliable is this prediction?
- What drives the uncertainty?
- How confident should I be in this analysis?
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np
from scipy import stats


class UncertaintyMetrics(BaseModel):
    """
    Container for uncertainty quantification metrics.
    
    All metrics designed to be interpretable and actionable:
    - Higher volatility = more uncertain outcome
    - Higher data quality = more reliable prediction
    - Higher confidence decay = prediction aging faster
    """
    
    volatility_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="0-100: Higher = more volatile distribution (higher variance, fat tails)"
    )
    
    data_quality_index: float = Field(
        ...,
        ge=0,
        le=100,
        description="0-100: Higher = better data coverage and recency"
    )
    
    confidence_decay: float = Field(
        ...,
        ge=0,
        le=1,
        description="0-1: Rate of confidence decay per day/time unit (higher = decays faster)"
    )
    
    # Metadata for transparency
    factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of contributing factors for each metric"
    )
    
    notes: str = Field(
        default="",
        description="Human-readable explanation of uncertainty drivers"
    )


def compute_volatility_score(
    distribution_values: np.ndarray,
    percentiles: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute volatility score (0-100) from distribution.
    
    Higher score indicates:
    - Higher variance
    - Fatter tails (high kurtosis)
    - More extreme outcomes possible
    
    Args:
        distribution_values: Raw distribution samples
        percentiles: Optional pre-computed percentiles (p5, p95 etc)
    
    Returns:
        Float 0-100 where higher = more volatile
    
    Algorithm:
    - Base: Coefficient of Variation (CV) = stdev/mean
    - Adjustment 1: IQR range (wider = more volatile)
    - Adjustment 2: Tail weight (kurtosis indicator)
    - Normalized to 0-100 scale
    """
    
    # Edge case: constant distribution (zero variance)
    if np.std(distribution_values) == 0:
        return 0.0  # No volatility
    
    # Compute basic statistics
    mean = np.mean(distribution_values)
    std = np.std(distribution_values, ddof=1)
    
    # Avoid division by zero for CV
    if abs(mean) < 1e-10:
        # For distributions centered near zero, use std directly
        cv = std * 100  # Scale up for scoring
    else:
        cv = std / abs(mean)
    
    # Compute IQR (Interquartile Range)
    if percentiles:
        p25 = percentiles.get('p25', np.percentile(distribution_values, 25))
        p75 = percentiles.get('p75', np.percentile(distribution_values, 75))
    else:
        p25, p75 = np.percentile(distribution_values, [25, 75])
    
    iqr = p75 - p25
    
    # Tail weight: measure extreme values
    p5, p95 = np.percentile(distribution_values, [5, 95])
    tail_range = p95 - p5
    tail_weight = tail_range / (iqr + 1e-10)  # Normalized tail spread
    
    # Compute kurtosis (excess kurtosis) with error handling
    try:
        kurt = stats.kurtosis(distribution_values)
        if np.isnan(kurt) or np.isinf(kurt):
            kurt = 0.0
    except:
        kurt = 0.0
    
    # Combine factors with adjusted weights
    # CV contributes up to 50 points, IQR up to 25, tail weight up to 15, kurtosis up to 10
    base_score = min(cv * 100, 50)  # CV scaled
    iqr_component = min(iqr * 50, 25)  # IQR contribution
    tail_component = min((tail_weight - 2.5) * 7.5, 15)  # Excess beyond normal
    tail_component = max(0, tail_component)  # No negative contribution
    kurt_component = min(abs(kurt) * 5, 10)  # Kurtosis contribution
    
    score = base_score + iqr_component + tail_component + kurt_component
    
    # Normalize to 0-100 range
    score = min(score, 100.0)
    score = max(score, 0.0)
    
    return float(score)


def compute_data_quality_index(
    features_present: Dict[str, bool],
    data_age_days: Optional[float] = None,
    sample_size: Optional[int] = None,
    required_features: Optional[list] = None
) -> float:
    """
    Compute data quality index (0-100).
    
    Higher score indicates:
    - More complete feature coverage
    - More recent data
    - Larger sample size
    
    Args:
        features_present: Dict of {feature_name: is_present}
        data_age_days: Age of data in days (0 = today)
        sample_size: Number of data points used
        required_features: List of critical features (optional)
    
    Returns:
        Float 0-100 where higher = better quality
    
    Algorithm:
    - Coverage: % of required features present (50% weight)
    - Recency: Exponential decay with age (30% weight)
    - Sample size: Log-scaled bonus (20% weight)
    """
    
    # Default required features if not specified
    if required_features is None:
        required_features = list(features_present.keys())
    
    # 1. Feature Coverage Score (0-50 points)
    total_required = len(required_features)
    if total_required == 0:
        coverage_score = 50.0  # No requirements = perfect coverage
    else:
        present_count = sum(
            1 for feat in required_features 
            if features_present.get(feat, False)
        )
        coverage_ratio = present_count / total_required
        coverage_score = coverage_ratio * 50
    
    # 2. Recency Score (0-30 points)
    # Exponential decay: fresh data = 30, 7 days = 20, 30 days = 10, >90 days = 0
    if data_age_days is None:
        recency_score = 15.0  # Neutral if unknown
    elif data_age_days <= 0:
        recency_score = 30.0  # Fresh data
    else:
        half_life_days = 14.0  # Data "half-life"
        decay_factor = 0.5 ** (data_age_days / half_life_days)
        recency_score = 30.0 * decay_factor
    
    # 3. Sample Size Score (0-20 points)
    # Logarithmic scaling: 10 samples = 5pts, 100 = 12pts, 1000 = 17pts, 10000 = 20pts
    if sample_size is None:
        sample_score = 10.0  # Neutral if unknown
    elif sample_size <= 0:
        sample_score = 0.0
    else:
        # Log scale with soft cap
        sample_score = min(20.0, 5.0 * np.log10(sample_size + 1))
    
    total_score = coverage_score + recency_score + sample_score
    
    # Ensure 0-100 bounds
    total_score = min(100.0, max(0.0, total_score))
    
    return float(total_score)


def compute_confidence_decay(
    volatility_score: float,
    data_age_days: float,
    event_horizon_days: float = 7.0
) -> float:
    """
    Compute confidence decay rate (0-1 per day).
    
    Higher value indicates:
    - Confidence degrades faster over time
    - Predictions become stale quicker
    
    Args:
        volatility_score: Volatility metric (0-100)
        data_age_days: Current age of underlying data
        event_horizon_days: Days until event (default 7)
    
    Returns:
        Float 0-1 representing decay rate per day
        
    Algorithm:
    - Base decay from volatility (volatile = decays faster)
    - Accelerated decay for stale data
    - Proximity to event affects decay
    """
    
    # Base decay from volatility
    # High volatility (80+) = 0.15/day, Medium (50) = 0.08/day, Low (20) = 0.03/day
    base_decay = 0.03 + (volatility_score / 100) * 0.12
    
    # Data staleness multiplier
    # Fresh data (0-2 days): 1.0x
    # Moderate (3-7 days): 1.2x
    # Stale (8-30 days): 1.5x
    # Very stale (>30 days): 2.0x
    if data_age_days <= 2:
        staleness_multiplier = 1.0
    elif data_age_days <= 7:
        staleness_multiplier = 1.2
    elif data_age_days <= 30:
        staleness_multiplier = 1.5
    else:
        staleness_multiplier = 2.0
    
    # Event proximity factor
    # Far future (>14 days): 0.8x (slower decay, more stable)
    # Near term (7-14 days): 1.0x (standard)
    # Imminent (<7 days): 1.3x (faster decay, more volatile)
    if event_horizon_days > 14:
        proximity_factor = 0.8
    elif event_horizon_days >= 7:
        proximity_factor = 1.0
    else:
        proximity_factor = 1.3
    
    decay_rate = base_decay * staleness_multiplier * proximity_factor
    
    # Cap at 0-1 range
    decay_rate = min(1.0, max(0.0, decay_rate))
    
    return float(decay_rate)


def compute_all_uncertainty_metrics(
    distribution_values: np.ndarray,
    features_present: Dict[str, bool],
    data_age_days: Optional[float] = None,
    sample_size: Optional[int] = None,
    event_horizon_days: float = 7.0,
    percentiles: Optional[Dict[str, float]] = None
) -> UncertaintyMetrics:
    """
    Compute all uncertainty metrics in one call.
    
    Args:
        distribution_values: Raw simulation distribution
        features_present: Feature availability dict
        data_age_days: Age of data (optional)
        sample_size: Data sample size (optional)
        event_horizon_days: Days until event
        percentiles: Pre-computed percentiles (optional)
    
    Returns:
        UncertaintyMetrics object with all metrics and factors
    """
    
    # Compute each metric
    volatility = compute_volatility_score(distribution_values, percentiles)
    data_quality = compute_data_quality_index(
        features_present,
        data_age_days,
        sample_size
    )
    confidence_decay = compute_confidence_decay(
        volatility,
        data_age_days or 0.0,
        event_horizon_days
    )
    
    # Build factor breakdown
    factors = {
        "distribution_cv": float(np.std(distribution_values, ddof=1) / np.mean(distribution_values)),
        "data_age_days": data_age_days or 0.0,
        "feature_coverage": sum(features_present.values()) / len(features_present) if features_present else 0.0,
        "sample_size": sample_size or 0,
        "event_horizon_days": event_horizon_days
    }
    
    # Generate notes
    notes_parts = []
    if volatility > 70:
        notes_parts.append("High volatility: wide range of possible outcomes")
    if data_quality < 50:
        notes_parts.append("Limited data quality: missing features or stale data")
    if confidence_decay > 0.15:
        notes_parts.append("Rapid confidence decay: prediction freshness critical")
    
    notes = "; ".join(notes_parts) if notes_parts else "Standard uncertainty profile"
    
    return UncertaintyMetrics(
        volatility_score=volatility,
        data_quality_index=data_quality,
        confidence_decay=confidence_decay,
        factors=factors,
        notes=notes
    )
