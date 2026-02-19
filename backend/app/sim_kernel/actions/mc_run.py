from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class MonteCarloAction(SimulationAction):
    name = "monte_carlo"
    priority = 50
    degradable = True

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        mc = ctx.services.get("mc_engine")
        if mc is None:
            state.warnings.append("mc_engine_not_wired")
            state.mc_result = {"error": "mc_engine_not_wired"}
            state.artifacts["mc"] = state.mc_result
            return state

        budget = ctx.services.get("_budget_decision")
        max_runs = getattr(budget, "mc_runs", config.budget.max_mc_runs)

        # Pass baseline rating/features if engine supports it; otherwise ignore.
        state.mc_result = mc(
            request=state.request,
            features=state.features,
            rating=state.rating,
            seed=int(config.seed),
            depth=str(config.depth),
            max_runs=int(max_runs),
        )
        state.artifacts["mc"] = state.mc_result
        return state
