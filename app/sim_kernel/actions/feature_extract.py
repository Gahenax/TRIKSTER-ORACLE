from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class FeatureExtractAction(SimulationAction):
    name = "feature_extract"
    priority = 90
    degradable = True

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # Wrapper: call existing feature extractor if available via services.
        extractor = ctx.services.get("feature_extractor")
        if extractor is None:
            # If not wired, do nothing (low friction).
            state.warnings.append("feature_extractor_not_wired")
            return state

        state.features = extractor(state.request, seed=int(config.seed), depth=str(config.depth))
        state.artifacts["features"] = state.features
        return state
