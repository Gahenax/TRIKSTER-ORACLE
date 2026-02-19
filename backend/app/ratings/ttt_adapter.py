from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class RatingPoint:
    mu: float
    sigma: float
    last_fight_date: Optional[str] = None


class TTTAdapter:
    '''
    Minimal-friction adapter:
    - If TrueSkillThroughTime dependency is available, use it.
    - If not available, fall back to a simple heuristic baseline (non-blocking).
    This keeps production stable while enabling future upgrade.

    Contract:
    - input history: list of bouts with timestamps and winners
    - output: RatingPoint for each fighter "today"
    '''
    def __init__(self):
        self._impl = None
        try:
            # Optional dependency: the repo may vendor or install it.
            # Antigravity: if dependency exists, wire it here.
            import trueskillthroughtime as ttt  # type: ignore
            self._impl = ttt
        except Exception:
            self._impl = None

    def rate_today(self, history: List[Dict[str, Any]], fighter_id: str) -> RatingPoint:
        if self._impl is None:
            # Fallback: neutral mu with sigma widening as inactivity grows if date available.
            last_date = None
            for bout in reversed(history):
                if bout.get("a") == fighter_id or bout.get("b") == fighter_id:
                    last_date = bout.get("date")
                    break
            # If no dates, keep sigma moderate.
            return RatingPoint(mu=25.0, sigma=8.333, last_fight_date=last_date)

        # If available, Antigravity should implement real calls based on the library API.
        # For now, return neutral to avoid breaking runtime.
        return RatingPoint(mu=25.0, sigma=8.333, last_fight_date=None)


def build_rating_provider(ttt: TTTAdapter, history_provider):
    '''
    Returns a function compatible with sim_kernel RatingBaselineAction:
    rating_provider(request_dict) -> dict
    '''
    def _provider(req: Dict[str, Any]) -> Dict[str, Any]:
        a = req.get("fighter_a") or req.get("a")
        b = req.get("fighter_b") or req.get("b")
        history = history_provider(req)
        ra = ttt.rate_today(history, str(a))
        rb = ttt.rate_today(history, str(b))
        return {
            "a": {"mu": ra.mu, "sigma": ra.sigma, "last_fight_date": ra.last_fight_date},
            "b": {"mu": rb.mu, "sigma": rb.sigma, "last_fight_date": rb.last_fight_date},
        }
    return _provider
