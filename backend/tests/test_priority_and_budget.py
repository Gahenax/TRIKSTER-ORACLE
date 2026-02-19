"""
Test Priority Scheduler and Budget Degradation
Tests for sim_kernel Phase 2 features
"""

from __future__ import annotations

from app.sim_kernel.config import SimulationConfig, Budget
from app.sim_kernel.state import SimulationState
from app.sim_kernel.kernel import TricksterKernel
from app.sim_kernel.actions.ingest import IngestAction
from app.sim_kernel.actions.rating_baseline import RatingBaselineAction
from app.sim_kernel.actions.mc_run import MonteCarloAction
from app.sim_kernel.actions.explain import ExplainAction
from app.sim_kernel.actions.emit import EmitAction


def test_priority_scheduler_executes_in_priority_order():
    """Verify that PRIORITY scheduler runs actions in descending priority order."""
    
    # Track execution order
    execution_order = []
    
    # Create custom actions with different priorities
    class TrackedIngestAction(IngestAction):
        def run(self, ctx, state, config):
            execution_order.append(("ingest", self.priority))
            return super().run(ctx, state, config)
    
    class TrackedRatingAction(RatingBaselineAction):
        def run(self, ctx, state, config):
            execution_order.append(("rating", self.priority))
            return super().run(ctx, state, config)
    
    class TrackedMCAction(MonteCarloAction):
        def run(self, ctx, state, config):
            execution_order.append(("mc", self.priority))
            return super().run(ctx, state, config)
    
    class TrackedEmitAction(EmitAction):
        def run(self, ctx, state, config):
            execution_order.append(("emit", self.priority))
            return super().run(ctx, state, config)
    
    # Mock services
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"p": 0.5, "max_runs": max_runs}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    cfg = SimulationConfig(scheduler="PRIORITY", seed=42, depth="standard")
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [
        TrackedEmitAction(),
        TrackedMCAction(),
        TrackedRatingAction(),
        TrackedIngestAction(),
    ]
    
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify execution order matches priorities (descending)
    # Expected: ingest(100) -> rating(80) -> mc(50) -> emit(10)
    assert len(execution_order) == 4
    assert execution_order[0][0] == "ingest"
    assert execution_order[1][0] == "rating"
    assert execution_order[2][0] == "mc"
    assert execution_order[3][0] == "emit"
    
    # Verify priorities are descending
    priorities = [p for _, p in execution_order]
    assert priorities == sorted(priorities, reverse=True)


def test_low_budget_reduces_mc_runs():
    """Verify that low time budget reduces MC runs and marks degraded."""
    
    # Mock services
    captured_max_runs = []
    
    def mc_engine(request, features, rating, seed, depth, max_runs):
        captured_max_runs.append(max_runs)
        return {"p": 0.5, "max_runs": max_runs}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    
    # Very low budget should trigger degradation
    low_budget = Budget(
        max_ms_total=200,  # Very tight - should reduce MC runs to 80
        max_mc_runs=1000,
        max_graph_nodes=40,
        max_explain_chars=2000
    )
    
    cfg = SimulationConfig(scheduler="FIFO", seed=42, depth="standard", budget=low_budget)
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [IngestAction(), MonteCarloAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify degradation was triggered
    assert journal.degraded is True
    assert journal.degrade_reason is not None
    assert "low_time_budget" in journal.degrade_reason
    
    # Verify MC runs were reduced
    assert len(captured_max_runs) == 1
    assert captured_max_runs[0] <= 80  # Should be capped


def test_low_budget_shortens_explanation():
    """Verify that low time budget shortens explanation chars."""
    
    # Mock services
    captured_max_chars = []
    
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"p": 0.5}
    
    def explainer(request, features, rating, mc_result, max_chars):
        captured_max_chars.append(max_chars)
        return {"summary": "X" * min(max_chars, 100)}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={
        "mc_engine": mc_engine,
        "explainer": explainer,
        "response_mapper": response_mapper
    })
    
    # Low budget should shorten explanation
    low_budget = Budget(
        max_ms_total=350,  # Should reduce explain_chars to 600
        max_mc_runs=500,
        max_graph_nodes=40,
        max_explain_chars=2000
    )
    
    cfg = SimulationConfig(scheduler="FIFO", seed=42, depth="standard", budget=low_budget)
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [IngestAction(), MonteCarloAction(), ExplainAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify explanation was shortened
    assert len(captured_max_chars) == 1
    assert captured_max_chars[0] <= 600


def test_normal_budget_no_degradation():
    """Verify that normal budget does not trigger degradation."""
    
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"p": 0.5}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    
    # Normal budget
    normal_budget = Budget(
        max_ms_total=2000,  # Plenty of time
        max_mc_runs=500,
        max_graph_nodes=40,
        max_explain_chars=2000
    )
    
    cfg = SimulationConfig(scheduler="FIFO", seed=42, depth="standard", budget=normal_budget)
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [IngestAction(), MonteCarloAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify no degradation
    assert journal.degraded is False
    assert journal.degrade_reason is None


def test_journal_tracks_step_timings():
    """Verify that journal records timing for each step."""
    
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"p": 0.5}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    cfg = SimulationConfig(scheduler="FIFO", seed=42, depth="standard")
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [IngestAction(), MonteCarloAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify journal has steps
    assert len(journal.steps) == 3
    
    # Verify each step has timing info
    for step in journal.steps:
        assert step.started_at_ms > 0
        assert step.ended_at_ms >= step.started_at_ms
        assert step.duration_ms >= 0
        assert step.status in ["OK", "SKIP", "DEGRADED", "FAIL"]
        assert len(step.inputs_hash) == 64  # SHA-256 hex
        assert len(step.outputs_hash) == 64


def test_failed_action_continues_pipeline():
    """Verify that a failed action doesn't crash the pipeline."""
    
    class FailingAction(MonteCarloAction):
        def run(self, ctx, state, config):
            raise ValueError("Simulated failure")
    
    def mc_engine(request, features, rating, seed, depth, max_runs):
        return {"p": 0.5}
    
    def response_mapper(state):
        return {"documents": [], "meta": {}}
    
    kernel = TricksterKernel(services={"mc_engine": mc_engine, "response_mapper": response_mapper})
    cfg = SimulationConfig(scheduler="FIFO", seed=42, depth="standard")
    st = SimulationState(request={"fighter_a": "A", "fighter_b": "B"})
    
    actions = [IngestAction(), FailingAction(), EmitAction()]
    st2, journal = kernel.run(actions, st, cfg)
    
    # Verify pipeline continued despite failure
    assert len(journal.steps) == 3
    
    # Verify failed step is recorded
    failed_step = journal.steps[1]
    assert failed_step.status == "FAIL"
    assert failed_step.error_type == "ValueError"
    assert "Simulated failure" in failed_step.error_message
