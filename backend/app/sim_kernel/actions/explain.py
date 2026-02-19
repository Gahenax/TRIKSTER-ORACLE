from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class ExplainAction(SimulationAction):
    name = "explain"
    priority = 30
    degradable = True

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        explainer = ctx.services.get("explainer")
        if explainer is None:
            state.warnings.append("explainer_not_wired")
            return state

        budget = ctx.services.get("_budget_decision")
        max_chars = getattr(budget, "explain_chars", config.budget.max_explain_chars)

        state.explanation = explainer(
            request=state.request,
            features=state.features,
            rating=state.rating,
            mc_result=state.mc_result,
            max_chars=int(max_chars),
        )
        state.artifacts["explanation"] = state.explanation
        return state
