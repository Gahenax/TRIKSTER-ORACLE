"""
Pydantic schemas for API request/response validation
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class EventInput(BaseModel):
    """Input schema for a sports event to analyze"""
    event_id: Optional[str] = Field(None, description="Event ID from database")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_rating: float = Field(..., ge=0, le=3000, description="Home team ELO rating")
    away_rating: float = Field(..., ge=0, le=3000, description="Away team ELO rating")
    home_advantage: Optional[float] = Field(100, ge=0, le=300, description="Home advantage bonus")
    sport: Optional[str] = Field("football", description="Sport type")
    
    @field_validator('home_team', 'away_team')
    @classmethod
    def validate_team_names(cls, v):
        if not v or len(v) < 2:
            raise ValueError("Team name must be at least 2 characters")
        return v.strip()


class SimulationConfig(BaseModel):
    """Configuration for Monte Carlo simulation"""
    n_simulations: int = Field(
        1000,
        ge=100,
        le=10000,
        description="Number of simulations (demo max: 1000)"
    )
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    confidence_levels: List[float] = Field(
        [0.95, 0.99],
        description="Confidence interval levels"
    )


class RiskInfo(BaseModel):
    """Risk assessment output"""
    score: float = Field(..., description="Risk score (0-100)")
    band: str = Field(..., description="Risk band: LOW/MEDIUM/HIGH")
    rationale: str = Field(..., description="Human-readable explanation")


class ScenarioInfo(BaseModel):
    """Scenario description"""
    name: str
    probability: float
    description: str


class SensitivityFactor(BaseModel):
    """Sensitivity analysis factor"""
    factor_name: str
    delta_probability: float
    impact_level: str  # LOW/MEDIUM/HIGH


class ExplanationOutput(BaseModel):
    """Interpretable explanation of results"""
    summary: str = Field(..., description="Executive summary (3-4 lines)")
    scenarios: List[ScenarioInfo] = Field(..., description="Key scenarios")
    caveats: List[str] = Field(..., description="Limitations and warnings")
    sensitivity: Optional[List[SensitivityFactor]] = Field(
        None,
        description="Sensitivity analysis (what-if)"
    )


class SimulationResult(BaseModel):
    """Complete simulation output"""
    event: EventInput
    config: SimulationConfig
    
    # Core probabilities
    prob_home: float = Field(..., ge=0, le=1)
    prob_draw: Optional[float] = Field(None, ge=0, le=1)
    prob_away: float = Field(..., ge=0, le=1)
    
    # Distribution data
    distribution: Dict[str, List[float]] = Field(
        ...,
        description="Histogram bins and frequencies"
    )
    
    # Confidence intervals
    confidence_intervals: Dict[str, Dict[str, float]] = Field(
        ...,
        description="CI ranges per confidence level"
    )
    
    # Risk assessment
    risk: RiskInfo
    
    # Explanation
    explanation: ExplanationOutput
    
    # Metadata
    model_version: str = Field(default="0.1.0")
    execution_time_ms: float
    cache_hit: bool = Field(default=False)


class ErrorResponse(BaseModel):
    """Structured error response"""
    error: str
    message: str
    details: Optional[Dict] = None
