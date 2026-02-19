from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .base import SimulationAction, ActionContext


def _find_triangle_cycle(nodes: List[str], edge_p: Dict[Tuple[str, str], float], threshold: float = 0.55) -> bool:
    # Detect a simple directed triangle where p(u>v) and p(v>w) and p(w>u) exceed threshold.
    n = len(nodes)
    for i in range(n):
        for j in range(n):
            if j == i:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue
                u, v, w = nodes[i], nodes[j], nodes[k]
                if edge_p.get((u, v), 0.0) >= threshold and edge_p.get((v, w), 0.0) >= threshold and edge_p.get((w, u), 0.0) >= threshold:
                    return True
    return False


class MatchupGraphAction(SimulationAction):
    name = "matchup_graph"
    priority = 70
    degradable = True

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        graph_builder = ctx.services.get("matchup_graph_builder")
        if graph_builder is None:
            state.warnings.append("matchup_graph_builder_not_wired")
            return state

        budget = ctx.services.get("_budget_decision")
        max_nodes = int(getattr(budget, "graph_nodes", config.budget.max_graph_nodes))

        graph = graph_builder(state.request, state.features, state.rating, max_nodes=max_nodes, seed=int(config.seed))
        # graph expected: {"nodes":[...], "edges":[{"u":..,"v":..,"p":..}, ...]}
        state.matchup_graph = graph
        state.artifacts["matchup_graph"] = graph

        nodes = list(graph.get("nodes") or [])
        edge_p: Dict[Tuple[str, str], float] = {}
        for e in graph.get("edges") or []:
            u = str(e.get("u"))
            v = str(e.get("v"))
            p = float(e.get("p") or 0.0)
            edge_p[(u, v)] = p

        if len(nodes) >= 3 and _find_triangle_cycle(nodes, edge_p):
            state.warnings.append("non_transitive_cycle_detected")

        return state
