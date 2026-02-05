"""
API routes for simulation endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import time
import hashlib
import json

from app.api.schemas import (
    EventInput,
    SimulationConfig,
    SimulationResult,
    ErrorResponse
)
from app.core.engine import simulate_event
from app.core.risk import assess_risk
from app.core.explain import explain

router = APIRouter(prefix="/api/v1", tags=["simulation"])

# Simple in-memory cache with TTL
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes


def _generate_cache_key(event: EventInput, config: SimulationConfig) -> str:
    """Generate deterministic cache key from inputs"""
    data = {
        "event": event.model_dump(exclude={"event_id"}),
        "config": config.model_dump(exclude={"seed"}),
        "seed": config.seed if config.seed is not None else "none"
    }
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def _get_from_cache(cache_key: str) -> Dict[str, Any] | None:
    """Retrieve from cache if not expired"""
    if cache_key in _cache:
        entry = _cache[cache_key]
        if time.time() - entry["timestamp"] < CACHE_TTL:
            return entry["data"]
        else:
            # Expired, remove
            del _cache[cache_key]
    return None


def _set_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """Store in cache with timestamp"""
    _cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }


@router.post("/simulate", response_model=SimulationResult)
async def simulate(
    event: EventInput,
    config: SimulationConfig | None = None
) -> SimulationResult:
    """
    Run Monte Carlo simulation for a sports event.
    
    This endpoint combines:
    - Monte Carlo simulation (engine.py)
    - Risk assessment (risk.py)
    - Human-readable explanation (explain.py)
    
    Returns complete analysis with probabilities, risk, and interpretation.
    
    **Educational Use Only**: This tool is for learning probability concepts.
    NOT for gambling or wagering purposes.
    """
    try:
        # Use default config if not provided
        if config is None:
            config = SimulationConfig()
        
        # Check cache
        cache_key = _generate_cache_key(event, config)
        cached_result = _get_from_cache(cache_key)
        
        if cached_result:
            return SimulationResult(**cached_result, cache_hit=True)
        
        # Run simulation
        sim_result = simulate_event(event, config)
        
        # Assess risk
        risk_info = assess_risk(
            probabilities={
                "home": sim_result["prob_home"],
                "draw": sim_result["prob_draw"],
                "away": sim_result["prob_away"]
            },
            distribution_data=sim_result["distribution"],
            confidence_intervals=sim_result["confidence_intervals"]
        )
        
        # Generate explanation
        explanation = explain(
            probabilities={
                "home": sim_result["prob_home"],
                "draw": sim_result["prob_draw"],
                "away": sim_result["prob_away"]
            },
            event=event,
            risk=risk_info,
            config=config
        )
        
        # Construct complete result
        result = SimulationResult(
            event=event,
            config=config,
            prob_home=sim_result["prob_home"],
            prob_draw=sim_result["prob_draw"],
            prob_away=sim_result["prob_away"],
            distribution=sim_result["distribution"],
            confidence_intervals=sim_result["confidence_intervals"],
            risk=risk_info,
            explanation=explanation,
            execution_time_ms=sim_result["execution_time_ms"],
            cache_hit=False
        )
        
        # Cache the result (convert to dict for caching)
        result_dict = result.model_dump()
        _set_to_cache(cache_key, result_dict)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {"field": "input_validation"}
            }
        )
    except Exception as e:
        # Log error in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SimulationError",
                "message": "An error occurred during simulation",
                "details": {"type": type(e).__name__}
            }
        )


@router.get("/cache/stats")
async def cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics (for monitoring/debugging).
    
    Returns:
    - total_entries: Number of cached results
    - expired_entries: Number of expired entries
    - cache_ttl: Cache TTL in seconds
    """
    current_time = time.time()
    total = len(_cache)
    expired = sum(
        1 for entry in _cache.values()
        if current_time - entry["timestamp"] >= CACHE_TTL
    )
    
    return {
        "total_entries": total,
        "active_entries": total - expired,
        "expired_entries": expired,
        "cache_ttl_seconds": CACHE_TTL
    }


@router.delete("/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear all cached simulation results.
    
    Useful for testing or when deploying new model versions.
    """
    _cache.clear()
    return {"status": "success", "message": "Cache cleared"}
