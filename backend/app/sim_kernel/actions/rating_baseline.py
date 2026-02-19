from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class RatingBaselineAction(SimulationAction):
    name = "rating_baseline"
    priority = 80
    degradable = True

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # Wrapper: call rating provider if available via services.
        provider = ctx.services.get("rating_provider")
        if provider is None:
            state.warnings.append("rating_provider_not_wired")
            return state

        state.rating = provider(state.request)
        state.artifacts["rating"] = state.rating
        return state
