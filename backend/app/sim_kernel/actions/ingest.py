from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class IngestAction(SimulationAction):
    name = "ingest"
    priority = 100
    degradable = False

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # Minimal validation; do not overreach.
        req = state.request
        if not isinstance(req, dict):
            raise ValueError("request must be a dict")
        # Ensure seed is attached to artifacts for deterministic downstream steps.
        state.artifacts.setdefault("meta", {})
        state.artifacts["meta"]["seed"] = int(config.seed)
        return state
