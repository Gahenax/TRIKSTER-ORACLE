from __future__ import annotations

from app.sim_kernel.config import SimulationConfig
from app.sim_kernel.state import SimulationState
from app.sim_kernel.kernel import TricksterKernel
from app.sim_kernel.actions.ingest import IngestAction
from app.sim_kernel.actions.matchup_graph import MatchupGraphAction
from app.sim_kernel.actions.emit import EmitAction


def test_cycle_warning_is_emitted():
    def graph_builder(request, features, rating, max_nodes, seed):
        return {
            "nodes": ["A", "B", "C"],
            "edges": [
                {"u": "A", "v": "B", "p": 0.6},
                {"u": "B", "v": "C", "p": 0.6},
                {"u": "C", "v": "A", "p": 0.6},
            ],
        }

    def response_mapper(state):
        return {"documents": [], "meta": {}}

    kernel = TricksterKernel(services={"matchup_graph_builder": graph_builder, "response_mapper": response_mapper})
    cfg = SimulationConfig(seed=1, scheduler="FIFO")
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    actions = [IngestAction(), MatchupGraphAction(), EmitAction()]
    st2, _ = kernel.run(actions, st, cfg)

    assert "non_transitive_cycle_detected" in st2.warnings
