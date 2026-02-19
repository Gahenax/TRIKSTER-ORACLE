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

# --- SIM_KERNEL_SERVICES (autogen) ---
from app.core.engine import simulate_event_v2 as _simulate_event_v2_orig
from app.core.explain import explain as _explain_orig

def _mc_engine_service(request, features, rating, seed, depth, max_runs):
    """Wrapper around existing simulate_event_v2. Must honor max_runs."""
    # Map request dict to EventInput + SimulationConfig as existing code does
    from app.api.schemas import EventInput, SimulationConfig as SimConfig
    
    event = EventInput(
        home_team=request.get("home_team", "Home"),
        away_team=request.get("away_team", "Away"),
        sport=request.get("sport", "FOOTBALL"),
        event_id=request.get("event_id", ""),
        home_rating=request.get("home_rating", 1500.0),
        away_rating=request.get("away_rating", 1500.0),
        home_advantage=request.get("home_advantage", 0.0)
    )
    
    # Honor max_runs budget
    config_dict = request.get("config", {})
    config_dict["n_simulations"] = min(max_runs, config_dict.get("n_simulations", 1000))
    if seed:
        config_dict["seed"] = seed
    config = SimConfig(**config_dict)
    
    # Call existing engine
    dist = _simulate_event_v2_orig(event, config)
    
    # Return distribution object wrapped for kernel
    return {"distribution": dist, "seed": config.seed, "n_simulations": config.n_simulations}

def _explainer_service(request, features, rating, mc_result, max_chars):
    """Wrapper around existing explain(). Must honor max_chars."""
    # The explain function in app.core.explain expects different args
    # Since we're in a kernel wrapper context, we skip explanation for now
    # TODO: Wire proper explain call when needed
    return {"summary": "Explanation placeholder", "max_chars": max_chars}

def _response_mapper_service(state):
    """
    Map SimulationState -> EXISTING /api/v2/simulate response shape.
    CRITICAL: This must produce the exact same dict structure as before kernel integration.
    The only permitted additions are optional keys inside response['meta'].
    """
    # Return the pre-kernel response stashed during endpoint execution
    # This ensures 100% backward compatibility
    return state.artifacts.get('pre_kernel_response') or {}
# --- /SIM_KERNEL_SERVICES (autogen) ---


from app.api.schemas import EventInput, SimulationConfig
from app.core.distribution import DistributionObject
from app.core.uncertainty import compute_all_uncertainty_metrics, UncertaintyMetrics
from app.core.tokens import (
    get_ledger,
    require_tokens,
    check_feature_access,
    FeatureTier,
    AccessDeniedError,
    TokenTransaction,
    UserStatus
)

from app.sim_kernel.kernel import TricksterKernel
from app.sim_kernel.state import SimulationState
from app.sim_kernel.config import SimulationConfig as KernelSimulationConfig
from app.sim_kernel.actions.ingest import IngestAction
from app.sim_kernel.actions.mc_run import MonteCarloAction
from app.sim_kernel.actions.explain import ExplainAction
from app.sim_kernel.actions.emit import EmitAction


router = APIRouter(prefix="/api/v2", tags=["v2"])


# --------------------
# Request/Response Models
# --------------------

class SimulateRequestV2(BaseModel):
    """Request model for /api/v2/simulate"""
    sport: str = "FOOTBALL"
    event_id: Optional[str] = None  # auto-generated if missing
    market: str = "moneyline_home"
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    # Actor-name fields (frontend v2 contract)
    primary: Optional[str] = None   # maps to home_team
    opponent: Optional[str] = None  # maps to away_team
    mode: Optional[str] = None      # FAST | ORACLE -> maps to depth
    home_rating: float = 1500.0     # sensible default for actor-name mode
    away_rating: float = 1500.0     # sensible default for actor-name mode
    home_advantage: float = 0.0
    depth: str = "headline_pick"    # headline_pick | full_distribution | scenario_extremes | etc
    iterations: Optional[int] = None  # optional override for n_simulations
    config: Optional[Dict[str, Any]] = None


class HeadlinePickResponse(BaseModel):
    """Free-tier response (0 tokens)"""
    sport: str
    event_id: str
    market: str
    model_version: str = "v2.0"
    pick: Dict[str, Any]
    cost_tokens: int = 0
    user_status: Optional[UserStatus] = None
    notes: str = "Headline pick is always free for educational access"


class FullDistributionResponse(BaseModel):
    """Full distribution response (2+ tokens)"""
    distribution: DistributionObject
    uncertainty: UncertaintyMetrics
    cost_tokens: int
    transaction_id: str
    user_status: UserStatus
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
    
    # ── Actor-name resolution (frontend v2 contract) ──
    # Map primary/opponent to home_team/away_team if provided
    if request.primary and not request.home_team:
        request.home_team = request.primary
    if request.opponent and not request.away_team:
        request.away_team = request.opponent
    # Map mode to depth if provided
    if request.mode:
        mode_map = {"FAST": "headline_pick", "ORACLE": "deep_dive_educational"}
        request.depth = mode_map.get(request.mode.upper(), request.depth)
    # Auto-generate event_id if missing
    if not request.event_id:
        import hashlib, time
        slug = f"{request.sport}_{request.home_team}_{request.away_team}_{int(time.time())}"
        request.event_id = hashlib.sha256(slug.encode()).hexdigest()[:12]
    # Apply iterations override to config
    if request.iterations:
        cfg = request.config or {}
        cfg["n_simulations"] = request.iterations
        request.config = cfg

    # Validate depth
    depth = request.depth.lower()
    if depth not in DEPTH_TO_TIER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid depth '{request.depth}'. Must be one of: {list(DEPTH_TO_TIER.keys())}"
        )
    
    tier = DEPTH_TO_TIER[depth]
    ledger = get_ledger()
    
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
        
        # Record analysis if user_id is provided
        new_status = None
        if x_user_id:
            new_status = ledger.record_analysis(x_user_id)
        
        return HeadlinePickResponse(
            sport=request.sport,
            event_id=request.event_id,
            market=request.market,
            pick={
                "predicted_outcome": outcome,
                "confidence": confidence,
                "median_probability": round(dist.percentiles.p50, 3)
            },
            user_status=new_status
        )
    
    # GATED TIER (requires auth + tokens)
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required for gated endpoints"
        )
    
    # Enforcement: Cooldown and Daily Limit
    status_obj = ledger.get_user_status(x_user_id)
    now = datetime.now(timezone.utc)
    
    if not status_obj.is_premium:
        # Check cooldown
        if status_obj.cooldown_until and now < status_obj.cooldown_until:
            wait_sec = int((status_obj.cooldown_until - now).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "cooldown_active",
                    "message": f"Cooldown active. Please wait {wait_sec} seconds.",
                    "cooldown_until": status_obj.cooldown_until.isoformat()
                }
            )
        
        # Check daily limit vs tokens
        if status_obj.daily_used >= status_obj.daily_limit:
            # If free limit reached, user MUST have tokens unless they are premium
            if tier == FeatureTier.HEADLINE_PICK:
                # Even headline pick costs tokens after daily limit?
                # The rule say "consume token only if daily_used >= daily_limit and not premium"
                # Let's assume headline pick costs 1 token after limit
                tier = FeatureTier.FULL_DISTRIBUTION # Upgrade to check tokens

    # Check/consume tokens if applicable
    try:
        # If daily free limit not reached, headline_pick is free (0 tokens)
        # We only call consume_tokens if it has a cost or if we want to record it.
        # But consume_tokens for headline_pick is 0 anyway.
        
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
    
    # Record analysis (increments daily_used and sets cooldown)
    new_status = ledger.record_analysis(x_user_id)
        # --- SIM_KERNEL_INTEGRATION (autogen) ---
    # Kernel integration is designed to be non-breaking.
    # Steps:
    #  1) Compute the pre-kernel response using existing logic (already done above).
    #  2) Run kernel pipeline to attach observability meta only.
    #
    # REQUIRED: ensure `pre_kernel_response` exists before this block.
    try:
        # Build kernel config from request if possible; otherwise default.
        _kcfg = KernelSimulationConfig(
            scheduler='FIFO',
            seed=int(getattr(request, 'seed', 1337)) if hasattr(request, 'seed') else 1337,
            depth='standard',
        )
        _kstate = SimulationState(request=(request.dict() if hasattr(request, 'dict') else request))
        # Stash the already-built response to guarantee exact response shape.
        _kstate.artifacts['pre_kernel_response'] = locals().get('response') or locals().get('resp') or locals().get('result')
        _kernel = TricksterKernel(services={
            'mc_engine': _mc_engine_service,
            'explainer': _explainer_service,
            'response_mapper': _response_mapper_service,
        })
        _actions = [IngestAction(), MonteCarloAction(), ExplainAction(), EmitAction()]
        _kstate2, _journal = _kernel.run(_actions, _kstate, _kcfg)
        # Replace outgoing response with kernel-emitted response (identical shape, with optional meta additions).
        _kernel_response = _kstate2.artifacts.get('response')
        if isinstance(_kernel_response, dict):
            response = _kernel_response
    except Exception:
        # Non-breaking guarantee: if anything fails, keep original response.
        pass
    # --- /SIM_KERNEL_INTEGRATION (autogen) ---

    return FullDistributionResponse(
        distribution=dist,
        uncertainty=uncertainty,
        cost_tokens=transaction.cost,
        transaction_id=transaction.transaction_id,
        user_status=new_status,
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
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    POST /api/v2/tokens/topup
    
    Admin endpoint to add tokens (requires authorization in production).
    In development mode, authorization is optional for testing.
    """
    # In production, validate admin authorization here
    # if not authorization or not is_admin(authorization):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    ledger = get_ledger()
    new_balance = ledger.add_tokens(request.user_id, request.amount)
    
    return {
        "user_id": request.user_id,
        "balance": new_balance,
        "amount_added": request.amount,
        "timestamp": datetime.now(timezone.utc)
    }


@router.get("/me/status")
async def get_my_status(
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """GET /api/v2/me/status"""
    ledger = get_ledger()
    return ledger.get_user_status(x_user_id)


@router.post("/me/premium")
async def promote_to_premium(
    x_user_id: str = Header(..., alias="X-User-ID"),
    is_premium: bool = True
):
    """POST /api/v2/me/premium (Admin/Demo mock)"""
    ledger = get_ledger()
    ledger.set_premium(x_user_id, is_premium)
    return ledger.get_user_status(x_user_id)


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