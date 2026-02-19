from __future__ import annotations

import json
from pathlib import Path

from app.sim_kernel.config import SimulationConfig
from app.sim_kernel.state import SimulationState
from app.sim_kernel.kernel import TricksterKernel
from app.sim_kernel.actions.ingest import IngestAction
from app.sim_kernel.actions.matchup_graph import MatchupGraphAction
from app.sim_kernel.actions.emit import EmitAction


def test_scenarios_runner_smoke():
    scenarios_dir = Path("tests/scenarios")
    scenarios = sorted(scenarios_dir.glob("*.json"))
    assert scenarios, "no scenarios found"

    # Minimal wiring for scenarios
    def graph_builder(request, features, rating, max_nodes, seed):
        # This builder can be overridden later per scenario; here a simple cycle to satisfy fixture.
        return {
            "nodes": ["A", "B", "C"],
            "edges": [
                {"u": "A", "v": "B", "p": 0.6},
                {"u": "B", "v": "C", "p": 0.6},
                {"u": "C", "v": "A", "p": 0.6}
            ]
        }

    def response_mapper(state):
        return {"documents": [], "meta": {}}

    kernel = TricksterKernel(services={"matchup_graph_builder": graph_builder, "response_mapper": response_mapper})
    actions = [IngestAction(), MatchupGraphAction(), EmitAction()]

    for sp in scenarios:
        data = json.loads(sp.read_text(encoding="utf-8"))
        cfg = SimulationConfig(**data.get("config", {}))
        st = SimulationState(request=data["request"])
        st2, _ = kernel.run(actions, st, cfg)
        expected = data.get("assert", {})
        for w in expected.get("warnings_contains", []):
            assert w in st2.warnings
