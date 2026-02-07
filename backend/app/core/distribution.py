"""
Distribution Object V2 - Full statistical distribution output
Part of M1: SIM_ENGINE_V2_DISTRIBUTIONS milestone

This module defines the enhanced distribution schema that returns
complete statistical information including percentiles, scenarios,
and distribution metrics.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np
from dataclasses import dataclass


class PercentileSet(BaseModel):
    """Percentile values for distribution analysis"""
    p5: float = Field(..., description="5th percentile")
    p25: float = Field(..., description="25th percentile (Q1)")
    p50: float = Field(..., description="50th percentile (median)")
    p75: float = Field(..., description="75th percentile (Q3)")
    p95: float = Field(..., description="95th percentile")


class Scenario(BaseModel):
    """Individual scenario result with explicit parameters"""
    scenario_type: str = Field(..., description="conservative | base | aggressive")
    parameters: Dict[str, float] = Field(..., description="Parameter deltas from base")
    prob_home: float = Field(..., ge=0, le=1)
    prob_draw: Optional[float] = Field(None, ge=0, le=1)
    prob_away: float = Field(..., ge=0, le=1)
    percentiles: PercentileSet
    notes: str = Field(..., description="Explains assumptions for this scenario")


class DistributionObject(BaseModel):
    """
    Complete distribution output per SIM_ENGINE_SPEC (M1).
    
    This is the core artifact that powers:
    - Uncertainty visualization
    - Risk assessment
    - Scenario comparison
    - Educational content
    """
    
    # Identity
    sport: str = Field(default="football", description="Sport type")
    event_id: Optional[str] = Field(None, description="Event identifier")
    market: str = Field(default="1X2", description="Market type (e.g., 1X2, Over/Under)")
    model_version: str = Field(default="v2.0.0", description="Model version")
    
    # Simulation metadata
    n_sims: int = Field(..., ge=100, description="Number of simulations executed")
    ci_level: float = Field(default=0.95, ge=0, le=1, description="Confidence interval level")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    
    # Statistical measures
    percentiles: PercentileSet = Field(..., description="Key percentiles")
    mean: float = Field(..., description="Mean of distribution")
    stdev: float = Field(..., ge=0, description="Standard deviation")
    skew: Optional[float] = Field(None, description="Skewness (optional)")
    kurtosis: Optional[float] = Field(None, description="Kurtosis (optional)")
    
    # Scenarios
    scenarios: List[Scenario] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Conservative, Base, Aggressive scenarios"
    )
    
    # Additional info
    notes: str = Field(..., description="Model assumptions and caveats")
    execution_time_ms: float = Field(..., ge=0)


@dataclass
class ScenarioParams:
    """Parameter adjustments for scenario generation"""
    name: str
    scale_multiplier: float
    variance_multiplier: float
    notes: str


def compute_percentiles(values: np.ndarray) -> PercentileSet:
    """
    Compute required percentiles from distribution.
    Ensures monotonicity: p5 <= p25 <= p50 <= p75 <= p95
    """
    p5, p25, p50, p75, p95 = np.percentile(values, [5, 25, 50, 75, 95])
    
    # Sanity check monotonicity
    assert p5 <= p25 <= p50 <= p75 <= p95, "Percentiles not monotonic!"
    
    return PercentileSet(
        p5=float(p5),
        p25=float(p25),
        p50=float(p50),
        p75=float(p75),
        p95=float(p95)
    )


def compute_distribution_stats(values: np.ndarray) -> Dict[str, float]:
    """
    Compute statistical moments from distribution.
    
    Returns:
        Dict with mean, stdev, skew, kurtosis
    """
    from scipy import stats
    
    return {
        "mean": float(np.mean(values)),
        "stdev": float(np.std(values, ddof=1)),  # Sample std
        "skew": float(stats.skew(values)),
        "kurtosis": float(stats.kurtosis(values))
    }


# Scenario parameter definitions
SCENARIO_DEFINITIONS = {
    "conservative": ScenarioParams(
        name="conservative",
        scale_multiplier=0.8,  # Tighter distribution
        variance_multiplier=0.7,
        notes="Conservative: tighter spread, emphasizes central tendency. Use when data quality is high."
    ),
    "base": ScenarioParams(
        name="base",
        scale_multiplier=1.0,  # Standard
        variance_multiplier=1.0,
        notes="Base: standard model parameters. Balanced risk/return assessment."
    ),
    "aggressive": ScenarioParams(
        name="aggressive",
        scale_multiplier=1.2,  # Wider distribution
        variance_multiplier=1.3,
        notes="Aggressive: wider spread, accounts for higher uncertainty. Use when volatility is expected."
    )
}
