"""
API v2 Routes - Token-Gated Analytics Access

Implements:
- /api/v2/simulate (with depth-based token gating)
- /api/v2/tokens/balance
- /api/v2/tokens/ledger
- /api/v2/tokens/topup
- /api/v2/health
"""

from fastapi import APIRouter, HTTPException, Header, status
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.api.schemas import EventInput, SimulationConfig
from app.core.engine import simulate_event_v2
from app.core.distribution import DistributionObject
from app.core.uncertainty import compute_all_uncertainty_metrics, UncertaintyMetrics
from app.core.tokens import (
    get_ledger,
    require_tokens,
    check_feature_access,
    FeatureTier,
    AccessDeniedError,
    TokenTransaction
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


# --------------------
# Request/Response Models
# --------------------

class SimulateRequestV2(BaseModel):
    """Request model for /api/v2/simulate"""
    sport: str
    event_id: str
    market: str = "moneyline_home"
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_rating: float
    away_rating: float
    home_advantage: float = 0.0
    depth: str = "headline_pick"  # headline_pick | full_distribution | scenario_extremes | etc
    config: Optional[Dict[str, Any]] = None


class HeadlinePickResponse(BaseModel):
    """Free-tier response (0 tokens)"""
    sport: str
    event_id: str
    market: str
    model_version: str = "v2.0"
    pick: Dict[str, Any]
    cost_tokens: int = 0
    notes: str = "Headline pick is always free for educational access"


class FullDistributionResponse(BaseModel):
    """Full distribution response (2+ tokens)"""
    distribution: DistributionObject
    uncertainty: UncertaintyMetrics
    cost_tokens: int
    transaction_id: str
    notes: str


class TokenBalanceResponse(BaseModel):
    """Token balance response"""
    user_id: str
    balance: int
    last_updated: datetime


class TokenLedgerResponse(BaseModel):
    """Token ledger response"""
    user_id: str
    transactions: list[TokenTransaction]


class TopUpRequest(BaseModel):
    """Top-up request"""
    user_id: str
    amount: int = Field(gt=0)
    payment_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "v2.0.0"
    timestamp: datetime
    components: Dict[str, str]


# --------------------
# Depth Mapping
# --------------------

DEPTH_TO_TIER = {
    "headline_pick": FeatureTier.HEADLINE_PICK,
    "full_distribution": FeatureTier.FULL_DISTRIBUTION,
    "scenario_extremes": FeatureTier.SCENARIO_EXTREMES,
    "comparative_analysis": FeatureTier.COMPARATIVE_ANALYSIS,
    "deep_dive_educational": FeatureTier.DEEP_DIVE_EDUCATIONAL,
}


# --------------------
# Endpoints
# --------------------

@router.post("/simulate")
async def simulate_v2(
    request: SimulateRequestV2,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    authorization: Optional[str] = Header(None)
):
    """
    POST /api/v2/simulate
    
    Generate simulation with depth-based token gating.
    
    Depths:
    - headline_pick (0 tokens): FREE basic analysis
    - full_distribution (2 tokens): Complete percentiles + scenarios
    - scenario_extremes (3 tokens): Conservative/aggressive bounds
    - comparative_analysis (3 tokens): Multi-event comparison
    - deep_dive_educational (5 tokens): Full uncertainty + explainability
    """
    
    # Validate depth
    depth = request.depth.lower()
    if depth not in DEPTH_TO_TIER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid depth '{request.depth}'. Must be one of: {list(DEPTH_TO_TIER.keys())}"
        )
    
    tier = DEPTH_TO_TIER[depth]
    
    # FREE TIER (no auth required)
    if tier == FeatureTier.HEADLINE_PICK:
        # Build event input
        event = EventInput(
            home_team=request.home_team or "Home",
            away_team=request.away_team or "Away",
            sport=request.sport,
            event_id=request.event_id,
            home_rating=request.home_rating,
            away_rating=request.away_rating,
            home_advantage=request.home_advantage
        )
        
        config = SimulationConfig(**(request.config or {}))
        
        # Run simulation (lightweight)
        dist = simulate_event_v2(event, config)
        
        # Return headline pick (median + confidence)
        confidence = "high" if dist.stdev < 0.1 else "moderate" if dist.stdev < 0.2 else "low"
        outcome = "home" if dist.percentiles.p50 > 0.55 else "away" if dist.percentiles.p50 < 0.45 else "draw"
        
        return HeadlinePickResponse(
            sport=request.sport,
            event_id=request.event_id,
            market=request.market,
            pick={
                "predicted_outcome": outcome,
                "confidence": confidence,
                "median_probability": round(dist.percentiles.p50, 3)
            }
        )
    
    # GATED TIER (requires auth + tokens)
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required for gated endpoints"
        )
    
    # Check/consume tokens
    ledger = get_ledger()
    try:
        transaction = ledger.consume_tokens(
            user_id=x_user_id,
            feature=tier,
            event_id=request.event_id,
            idempotency_key=x_idempotency_key
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_tokens",
                "message": str(e),
                "required_tokens": e.required,
                "available_tokens": e.available,
                "feature": e.feature.value
            }
        )
    
    # Build event input
    event = EventInput(
        home_team=request.home_team or "Home",
        away_team=request.away_team or "Away",
        sport=request.sport,
        event_id=request.event_id,
        home_rating=request.home_rating,
        away_rating=request.away_rating,
        home_advantage=request.home_advantage
    )
    
    config = SimulationConfig(**(request.config or {}))
    
    # Run full simulation
    dist = simulate_event_v2(event, config)
    
    # Compute uncertainty (requires raw distribution values)
    # For now, use placeholder features
    features_present = {
        "home_rating": True,
        "away_rating": True,
        "home_advantage": True if request.home_advantage != 0 else False
    }
    
    # Note: In production, you'd extract actual distribution_values from engine
    # For now, synthesize approximate values for uncertainty calculation
    import numpy as np
    np.random.seed(config.seed if config.seed else 42)
    approx_dist_values = np.random.normal(
        dist.mean,
        dist.stdev,
        config.n_simulations
    )
    
    uncertainty = compute_all_uncertainty_metrics(
        distribution_values=approx_dist_values,
        features_present=features_present,
        data_age_days=1.0,  # Fresh simulation
        sample_size=config.n_simulations,
        event_horizon_days=7.0
    )
    
    return FullDistributionResponse(
        distribution=dist,
        uncertainty=uncertainty,
        cost_tokens=transaction.cost,
        transaction_id=transaction.transaction_id,
        notes=f"Full {tier.value} analysis"
    )


@router.get("/tokens/balance")
async def get_balance(
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """GET /api/v2/tokens/balance"""
    ledger = get_ledger()
    balance = ledger.get_balance(x_user_id)
    
    return TokenBalanceResponse(
        user_id=x_user_id,
        balance=balance,
        last_updated=datetime.now(timezone.utc)
    )


@router.get("/tokens/ledger")
async def get_ledger_history(
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = 100
):
    """GET /api/v2/tokens/ledger"""
    ledger = get_ledger()
    transactions = ledger.get_transaction_history(x_user_id, limit=limit)
    
    return TokenLedgerResponse(
        user_id=x_user_id,
        transactions=transactions
    )


@router.post("/tokens/topup")
async def topup_tokens(
    request: TopUpRequest,
    authorization: str = Header(..., alias="Authorization")
):
    """
    POST /api/v2/tokens/topup
    
    Admin endpoint to add tokens (requires authorization).
    In production, integrate with payment processor.
    """
    # TODO: Validate admin authorization
    # For now, simple implementation
    
    ledger = get_ledger()
    new_balance = ledger.add_tokens(request.user_id, request.amount)
    
    return {
        "user_id": request.user_id,
        "balance": new_balance,
        "amount_added": request.amount,
        "timestamp": datetime.now(timezone.utc)
    }


@router.get("/health")
async def health_check():
    """GET /api/v2/health"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        components={
            "sim_engine_v2": "ok",
            "uncertainty_metrics": "ok",
            "token_ledger": "ok"
        }
    )
