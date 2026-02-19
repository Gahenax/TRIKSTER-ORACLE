from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
import os

# Ensure the 'oracle' module in the root is importable
# This is a bit of a hack for the MVP structure provided in the prompt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from oracle.pipeline import evaluate_oracle_request

router = APIRouter(prefix="/api/oracle", tags=["Oracle"])

@router.post("/evaluate")
async def evaluate(request: Dict[str, Any]):
    """
    Oracle Pipeline Endpoint.
    Analyzes sports matchups using Monte Carlo simulations and returns a structured verdict.
    """
    try:
        # Basic validation
        if not request.get("primary") or not request.get("opponent"):
            raise HTTPException(status_code=400, detail="Primary and opponent actors are required.")
            
        result = evaluate_oracle_request(request)
        return result
    except Exception as e:
        # In production, we'd log the traceback
        raise HTTPException(status_code=500, detail=str(e))
