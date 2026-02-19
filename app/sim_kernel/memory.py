from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from .config import SimulationConfig


@dataclass
class BudgetDecision:
    mc_runs: int
    explain_chars: int
    graph_nodes: int
    degraded: bool
    reason: Optional[str]


def first_fit_v1(config: SimulationConfig) -> BudgetDecision:
    # Partition concept:
    # P1 ingest/validate (not modeled here)
    # P2 features/rating (not degraded initially)
    # P3 monte carlo (degradable)
    # P4 explanation (degradable)
    # This is a minimal allocator; it does not estimate time precisely, only caps.
    b = config.budget
    mc_runs = b.max_mc_runs
    explain_chars = b.max_explain_chars
    graph_nodes = b.max_graph_nodes

    degraded = False
    reason = None

    # Example: if budget is very small, shorten explain first
    if b.max_ms_total < 400:
        explain_chars = min(explain_chars, 600)
        degraded = True
        reason = "low_time_budget_short_explain"

    if b.max_ms_total < 250:
        mc_runs = min(mc_runs, 80)
        degraded = True
        reason = reason or "low_time_budget_reduce_mc"

    return BudgetDecision(mc_runs=mc_runs, explain_chars=explain_chars, graph_nodes=graph_nodes,
                         degraded=degraded, reason=reason)
