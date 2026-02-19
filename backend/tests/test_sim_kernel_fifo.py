from __future__ import annotations

from app.sim_kernel.config import SimulationConfig
from app.sim_kernel.state import SimulationState
from app.sim_kernel.kernel import TricksterKernel
from app.sim_kernel.actions.ingest import IngestAction
from app.sim_kernel.actions.mc_run import MonteCarloAction
from app.sim_kernel.actions.emit import EmitAction


def test_kernel_fifo_executes_and_returns_response_shape():
    # Minimal services: wire MC and mapper to avoid brittle assumptions.
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"seed": seed, "max_runs": max_runs, "p": 0.5}

    def response_mapper(state):
        # Mimic typical Trickster response fields (keep minimal).
        return {"documents": [{"p": state.mc_result.get("p"), "existing": False}]}

    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    cfg = SimulationConfig(scheduler="FIFO", seed=123, depth="standard")
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    actions = [IngestAction(), MonteCarloAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)

    resp = st2.artifacts.get("response")
    assert isinstance(resp, dict)
    assert "documents" in resp
    assert "meta" in resp
    assert "run_id" in resp["meta"]
    assert journal.steps[0].name == "ingest"
