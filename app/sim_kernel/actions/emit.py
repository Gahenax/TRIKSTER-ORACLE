from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class EmitAction(SimulationAction):
    name = "emit"
    priority = 10
    degradable = False

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # This action should map internal artifacts to the API response contract.
        # Low-friction rule: preserve existing response shape by deferring to a mapper if provided.
        mapper = ctx.services.get("response_mapper")
        if mapper is not None:
            resp = mapper(state)
        else:
            # Minimal generic response to avoid crashes; endpoint should replace with actual mapper.
            resp = {"ok": True, "documents": [], "meta": state.artifacts.get("meta", {})}

        # Always allow optional fields without breaking shape.
        resp.setdefault("meta", {})
        resp["meta"]["run_id"] = ctx.services.get("_run_id") or getattr(ctx.services.get("_journal"), "run_id", None)
        resp["meta"]["degraded"] = bool(getattr(state, "degraded", False))
        if getattr(state, "degrade_reason", None):
            resp["meta"]["degrade_reason"] = state.degrade_reason
        if getattr(state, "warnings", None):
            resp["meta"]["warnings"] = list(state.warnings)

        # Attach to state.artifacts for kernel return path.
        state.artifacts["response"] = resp
        return state
