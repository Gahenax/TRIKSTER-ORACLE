from typing import Dict, Any
from pydantic import BaseModel, Field, validator

class TailPercentiles(BaseModel):
    p5: float
    p10: float
    p25: float

class RiskEvaluationResult(BaseModel):
    """
    Contract Shape Guard for simulation results.
    Ensures stability of the output data structure.
    """
    pls: float = Field(..., ge=0.0, le=1.0)
    zone: str = Field(..., pattern="^(GREEN|YELLOW|RED)$")
    fragility: float
    tail_percentiles: TailPercentiles
    n_sims: int
    determinism_signature: str
    snapshot_id: str

    @validator('determinism_signature')
    def validate_hash(cls, v):
        if len(v) != 64:
            raise ValueError("Signature must be a 64-char hex hash")
        return v
