#!/usr/bin/env python3
"""
ANTIGRAVITY EXECUTION PROMPT (Python)
Project: Trickster Oracle
Goal: Integrate "kernel mindset" (step/action pipeline + journal + schedulers + budgets/degrade),
      then TrueSkill Through Time baseline, then discrete-event execution formalization, then
      non-transitivity detection + scenario regression — with MINIMUM FRICTION.

Hard constraints:
- Do NOT break existing API response shape for /simulate (only add optional fields).
- Prefer wrappers around existing logic, not rewrites.
- Every phase must ship with tests that prove non-regression.
- Determinism: same input + same seed => stable output (hash-stable artifacts).
- Observability: per-run journal with step records (timings, hashes, status, error).
- Degradation: if resource budget insufficient, degrade gracefully, mark degraded=True, provide reason.

How to use:
- You are Antigravity inside the repo root.
- Execute this plan sequentially.
- After each phase:
  1) run tests
  2) if failures: fix with smallest change
  3) commit with a clear message
- Do not refactor unrelated code.

Deliverables:
- New module app/sim_kernel with config/state/journal/kernel/scheduler/actions/memory.
- Endpoint /simulate routed through Kernel FIFO initially.
- Priority scheduler + budget degrade.
- TTT adapter integrated as baseline (mu/sigma "today").
- Optional discrete-event queue implementation (internal) backed by same journal.
- Non-transitivity detector on a local matchup graph (triangles/cycles).
- Scenario-based regression tests under tests/scenarios.

Notes:
- If project already has journaling tables/DB support, reuse it. Otherwise implement journaling in-memory
  and optionally persist to existing run repository if present.
- Keep scope tight: wrappers first, deeper enhancements later.
"""

from __future__ import annotations

import os
import re
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(".").resolve()


# ----------------------------
# Helpers (lightweight, no deps)
# ----------------------------

def sha256_json(obj: Any) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    except TypeError:
        payload = json.dumps(str(obj), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")

def append_if_missing(path: Path, needle: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        text += ("\n" if not text.endswith("\n") else "") + addition
        path.write_text(text, encoding="utf-8")

def find_file_by_regex(pattern: str, search_root: Path) -> List[Path]:
    rx = re.compile(pattern)
    hits: List[Path] = []
    for p in search_root.rglob("*.py"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if rx.search(t):
            hits.append(p)
    return hits

def log(msg: str) -> None:
    print(msg)


# ----------------------------
# Phase 0: Identify anchors
# ----------------------------

def phase0_discover_anchors() -> Dict[str, Any]:
    """
    Discover likely anchors for /simulate endpoint and existing orchestration.
    If ambiguous, choose the most likely and proceed with minimal change.

    This function does not modify code; it only prints findings and returns a dict.
    """
    anchors: Dict[str, Any] = {}

    # Find FastAPI endpoints referencing "/simulate"
    simulate_hits = find_file_by_regex(r'"/simulate"|\'/simulate\'', REPO_ROOT / "app")
    anchors["simulate_endpoint_candidates"] = [str(p) for p in simulate_hits]

    # Try to find function names that hint MC/explain/orchestrator
    mc_hits = find_file_by_regex(r"\bMonte\s*Carlo\b|monte_carlo|mc_run|simulate_mc", REPO_ROOT / "app")
    anchors["mc_candidates"] = [str(p) for p in mc_hits]

    explain_hits = find_file_by_regex(r"\bexplain\b|explanation|build_explain|generate_explain", REPO_ROOT / "app")
    anchors["explain_candidates"] = [str(p) for p in explain_hits]

    orchestrator_hits = find_file_by_regex(r"\borchestrator\b|pipeline|run_simulation|simulate\(", REPO_ROOT / "app")
    anchors["orchestrator_candidates"] = [str(p) for p in orchestrator_hits]

    log("PHASE 0 - Anchor Discovery Results")
    for k, v in anchors.items():
        log(f"- {k}: {len(v)}")
        for item in v[:10]:
            log(f"  - {item}")
        if len(v) > 10:
            log("  - ...")

    return anchors


# ----------------------------
# Phase 1: Kernel FIFO + Journal (wrappers)
# ----------------------------

KERNEL_FILES: Dict[str, str] = {}

KERNEL_FILES["app/sim_kernel/__init__.py"] = """\
"""

KERNEL_FILES["app/sim_kernel/config.py"] = """\
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional


SchedulerKind = Literal["FIFO", "PRIORITY", "ROUND_ROBIN"]
DepthKind = Literal["lite", "standard", "full"]


class Budget(BaseModel):
    max_ms_total: int = Field(default=2000, ge=50)
    max_mc_runs: int = Field(default=500, ge=1)
    max_graph_nodes: int = Field(default=40, ge=0)
    max_explain_chars: int = Field(default=2000, ge=0)


class SimulationConfig(BaseModel):
    scheduler: SchedulerKind = "FIFO"
    depth: DepthKind = "standard"
    seed: int = 1337
    quantum_ms: Optional[int] = None  # Only for ROUND_ROBIN
    budget: Budget = Budget()
    scenario_id: Optional[str] = None
"""

KERNEL_FILES["app/sim_kernel/state.py"] = """\
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SimulationState:
    request: Dict[str, Any]
    features: Optional[Dict[str, Any]] = None
    rating: Optional[Dict[str, Any]] = None
    matchup_graph: Optional[Dict[str, Any]] = None
    mc_result: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None

    warnings: List[str] = field(default_factory=list)
    degraded: bool = False
    degrade_reason: Optional[str] = None

    artifacts: Dict[str, Any] = field(default_factory=dict)
"""

KERNEL_FILES["app/sim_kernel/journal.py"] = """\
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class StepRecord:
    name: str
    status: str  # OK | SKIP | DEGRADED | FAIL
    started_at_ms: int
    ended_at_ms: int
    duration_ms: int
    inputs_hash: str
    outputs_hash: str
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class RunJournal:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    config_hash: str = ""
    started_at_ms: int = field(default_factory=_now_ms)
    ended_at_ms: int = 0
    duration_ms_total: int = 0
    degraded: bool = False
    degrade_reason: Optional[str] = None
    steps: List[StepRecord] = field(default_factory=list)

    def close(self) -> None:
        self.ended_at_ms = _now_ms()
        self.duration_ms_total = max(0, self.ended_at_ms - self.started_at_ms)
"""

KERNEL_FILES["app/sim_kernel/actions/base.py"] = """\
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ActionContext:
    # Optional container for shared services (repos, clients, etc)
    services: Dict[str, Any]


class SimulationAction:
    name: str = "base"
    priority: int = 50
    degradable: bool = False

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        raise NotImplementedError
"""

KERNEL_FILES["app/sim_kernel/scheduler.py"] = """\
from __future__ import annotations

from typing import List
from .actions.base import SimulationAction
from .config import SimulationConfig


class FIFOScheduler:
    def order(self, actions: List[SimulationAction], config: SimulationConfig) -> List[SimulationAction]:
        return actions


class PriorityScheduler:
    def order(self, actions: List[SimulationAction], config: SimulationConfig) -> List[SimulationAction]:
        return sorted(actions, key=lambda a: getattr(a, "priority", 50), reverse=True)


def get_scheduler(config: SimulationConfig):
    if config.scheduler == "FIFO":
        return FIFOScheduler()
    if config.scheduler == "PRIORITY":
        return PriorityScheduler()
    # ROUND_ROBIN reserved for future batch runs
    return FIFOScheduler()
"""

KERNEL_FILES["app/sim_kernel/memory.py"] = """\
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
"""

KERNEL_FILES["app/sim_kernel/kernel.py"] = """\
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .actions.base import ActionContext, SimulationAction
from .config import SimulationConfig
from .journal import RunJournal, StepRecord
from .memory import first_fit_v1
from .scheduler import get_scheduler
import time
import json
import hashlib


def _hash(obj: Any) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    except Exception:
        payload = str(obj).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class TricksterKernel:
    def __init__(self, services: Dict[str, Any] | None = None):
        self.services = services or {}

    def run(self, actions: List[SimulationAction], state: Any, config: SimulationConfig) -> Tuple[Any, RunJournal]:
        journal = RunJournal()
        journal.config_hash = _hash(config.model_dump())

        budget_decision = first_fit_v1(config)
        if getattr(state, "degraded", False) or budget_decision.degraded:
            state.degraded = True
            state.degrade_reason = state.degrade_reason or budget_decision.reason

        scheduler = get_scheduler(config)
        ordered = scheduler.order(actions, config)

        ctx = ActionContext(services=self.services)

        for action in ordered:
            started = int(time.time() * 1000)
            inputs_hash = _hash({"state": getattr(state, "__dict__", str(state)), "config": config.model_dump(), "action": action.name})

            status = "OK"
            err_t = None
            err_m = None
            warnings: List[str] = []

            try:
                # Allow actions to read budget decision via services (simple, low-friction)
                self.services.setdefault("_budget_decision", budget_decision)
                state = action.run(ctx, state, config)
            except Exception as e:
                status = "FAIL"
                err_t = type(e).__name__
                err_m = str(e)[:500]
                # Do not explode: keep partial state, but record the failure.
                warnings.append(f"step_failed:{action.name}")

            ended = int(time.time() * 1000)
            outputs_hash = _hash(getattr(state, "__dict__", str(state)))

            journal.steps.append(StepRecord(
                name=action.name,
                status=status,
                started_at_ms=started,
                ended_at_ms=ended,
                duration_ms=max(0, ended - started),
                inputs_hash=inputs_hash,
                outputs_hash=outputs_hash,
                error_type=err_t,
                error_message=err_m,
                warnings=warnings,
            ))

            # If a critical step fails, keep going unless it blocks emitting a response.
            # Actions should be coded to tolerate missing upstream artifacts.

        journal.degraded = bool(getattr(state, "degraded", False))
        journal.degrade_reason = getattr(state, "degrade_reason", None)
        journal.close()
        return state, journal
"""

KERNEL_FILES["app/sim_kernel/actions/ingest.py"] = """\
from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class IngestAction(SimulationAction):
    name = "ingest"
    priority = 100
    degradable = False

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # Minimal validation; do not overreach.
        req = state.request
        if not isinstance(req, dict):
            raise ValueError("request must be a dict")
        # Ensure seed is attached to artifacts for deterministic downstream steps.
        state.artifacts.setdefault("meta", {})
        state.artifacts["meta"]["seed"] = int(config.seed)
        return state
"""

KERNEL_FILES["app/sim_kernel/actions/feature_extract.py"] = """\
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
"""

KERNEL_FILES["app/sim_kernel/actions/rating_baseline.py"] = """\
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
"""

KERNEL_FILES["app/sim_kernel/actions/mc_run.py"] = """\
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
"""

KERNEL_FILES["app/sim_kernel/actions/explain.py"] = """\
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
"""

KERNEL_FILES["app/sim_kernel/actions/emit.py"] = """\
from __future__ import annotations

from typing import Any
from .base import SimulationAction, ActionContext


class EmitAction(SimulationAction):
    name = "emit"
    priority = 10
    degradable = False

    def run(self, ctx: ActionContext, state: Any, config: Any) -> Any:
        # This action should map internal artifacts to the API response contract.
        # Low-friction rule: preserve existing response shape by deferring to a mapper if provided.
        mapper = ctx.services.get("response_mapper")
        if mapper is not None:
            resp = mapper(state)
        else:
            # Minimal generic response to avoid crashes; endpoint should replace with actual mapper.
            resp = {"ok": True, "documents": [], "meta": state.artifacts.get("meta", {})}

        # Always allow optional fields without breaking shape.
        resp.setdefault("meta", {})
        resp["meta"]["run_id"] = ctx.services.get("_run_id") or getattr(ctx.services.get("_journal"), "run_id", None)
        resp["meta"]["degraded"] = bool(getattr(state, "degraded", False))
        if getattr(state, "degrade_reason", None):
            resp["meta"]["degrade_reason"] = state.degrade_reason
        if getattr(state, "warnings", None):
            resp["meta"]["warnings"] = list(state.warnings)

        # Attach to state.artifacts for kernel return path.
        state.artifacts["response"] = resp
        return state
"""

KERNEL_FILES["tests/test_sim_kernel_fifo.py"] = """\
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
"""

def phase1_create_kernel_files() -> None:
    for rel, content in KERNEL_FILES.items():
        write_file(REPO_ROOT / rel, content)
    log("PHASE 1 - Created sim_kernel module skeleton and basic test.")


# ----------------------------
# Phase 1.5: Wire /simulate endpoint (manual mapping)
# ----------------------------

def phase1_wire_endpoint_instructions() -> None:
    """
    Antigravity MUST implement wiring based on actual repo structure.
    This function prints precise instructions. Do the edits in-code accordingly.
    """
    log("\nPHASE 1.5 - WIRING INSTRUCTIONS (you must implement edits in the correct files):")
    log("1) Locate FastAPI route for /simulate (see Phase 0 candidates).")
    log("2) Replace direct orchestration with kernel execution:")
    log("   - Build SimulationConfig from request parameters (seed/depth optional).")
    log("   - Build SimulationState(request=payload_dict).")
    log("   - Create TricksterKernel(services={...}) wiring existing components:")
    log("       services['feature_extractor'] = existing_feature_extractor (if exists)")
    log("       services['mc_engine'] = existing_monte_carlo_engine")
    log("       services['explainer'] = existing_explanation_builder (if exists)")
    log("       services['response_mapper'] = function that maps SimulationState -> current API response shape")
    log("   - Run actions: ingest, feature_extract (if possible), rating_baseline (optional placeholder), monte_carlo, explain, emit")
    log("3) Return state.artifacts['response'] as the HTTP response.")
    log("4) Ensure API response shape unchanged; only add optional meta fields if allowed.")
    log("5) Run full test suite.")


# ----------------------------
# Phase 2: Priority scheduler + budgets/degrade (already scaffolded)
# ----------------------------

def phase2_instructions() -> None:
    log("\nPHASE 2 - PRIORITY + BUDGETS/DEGRADE")
    log("1) Ensure SimulationConfig.budget is actually derived from request defaults.")
    log("2) In mc_engine wrapper, accept max_runs and honor it.")
    log("3) In explainer wrapper, accept max_chars and honor it (short mode).")
    log("4) Switch scheduler to PRIORITY in config when requested (do not change default).")
    log("5) Add tests:")
    log("   - low budget reduces mc_runs and marks degraded")
    log("   - priority runs ingest before mc")
    log("6) No refactors beyond what's needed.")


# ----------------------------
# Phase 3: TrueSkill Through Time adapter
# ----------------------------

TTT_FILES: Dict[str, str] = {}

TTT_FILES["app/ratings/__init__.py"] = """\
"""

TTT_FILES["app/ratings/ttt_adapter.py"] = """\
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class RatingPoint:
    mu: float
    sigma: float
    last_fight_date: Optional[str] = None


class TTTAdapter:
    '''
    Minimal-friction adapter:
    - If TrueSkillThroughTime dependency is available, use it.
    - If not available, fall back to a simple heuristic baseline (non-blocking).
    This keeps production stable while enabling future upgrade.

    Contract:
    - input history: list of bouts with timestamps and winners
    - output: RatingPoint for each fighter "today"
    '''
    def __init__(self):
        self._impl = None
        try:
            # Optional dependency: the repo may vendor or install it.
            # Antigravity: if dependency exists, wire it here.
            import trueskillthroughtime as ttt  # type: ignore
            self._impl = ttt
        except Exception:
            self._impl = None

    def rate_today(self, history: List[Dict[str, Any]], fighter_id: str) -> RatingPoint:
        if self._impl is None:
            # Fallback: neutral mu with sigma widening as inactivity grows if date available.
            last_date = None
            for bout in reversed(history):
                if bout.get("a") == fighter_id or bout.get("b") == fighter_id:
                    last_date = bout.get("date")
                    break
            # If no dates, keep sigma moderate.
            return RatingPoint(mu=25.0, sigma=8.333, last_fight_date=last_date)

        # If available, Antigravity should implement real calls based on the library API.
        # For now, return neutral to avoid breaking runtime.
        return RatingPoint(mu=25.0, sigma=8.333, last_fight_date=None)


def build_rating_provider(ttt: TTTAdapter, history_provider):
    '''
    Returns a function compatible with sim_kernel RatingBaselineAction:
    rating_provider(request_dict) -> dict
    '''
    def _provider(req: Dict[str, Any]) -> Dict[str, Any]:
        a = req.get("fighter_a") or req.get("a")
        b = req.get("fighter_b") or req.get("b")
        history = history_provider(req)
        ra = ttt.rate_today(history, str(a))
        rb = ttt.rate_today(history, str(b))
        return {
            "a": {"mu": ra.mu, "sigma": ra.sigma, "last_fight_date": ra.last_fight_date},
            "b": {"mu": rb.mu, "sigma": rb.sigma, "last_fight_date": rb.last_fight_date},
        }
    return _provider
"""

TTT_FILES["tests/test_ttt_adapter_contract.py"] = """\
from __future__ import annotations

from app.ratings.ttt_adapter import TTTAdapter, build_rating_provider


def test_ttt_adapter_fallback_contract():
    ttt = TTTAdapter()

    def history_provider(req):
        return [{"a": "A", "b": "B", "winner": "A", "date": "2025-01-01"}]

    provider = build_rating_provider(ttt, history_provider)
    out = provider({"fighter_a": "A", "fighter_b": "B"})
    assert "a" in out and "b" in out
    assert "mu" in out["a"] and "sigma" in out["a"]
"""

def phase3_create_ttt_files() -> None:
    for rel, content in TTT_FILES.items():
        write_file(REPO_ROOT / rel, content)
    log("PHASE 3 - Created ratings/ttt_adapter scaffolding + contract test.")


def phase3_instructions() -> None:
    log("\nPHASE 3 - TTT INTEGRATION INSTRUCTIONS")
    log("1) Implement a history_provider that returns bout history with timestamps for the two fighters.")
    log("2) Wire rating_provider into TricksterKernel services:")
    log("   services['rating_provider'] = build_rating_provider(TTTAdapter(), history_provider)")
    log("3) In MC engine, incorporate rating prior minimally:")
    log("   - Use mu/sigma to set baseline p or adjust scenario parameters (small influence first).")
    log("4) Add warning if sigma is high (uncertainty) or long inactivity.")


# ----------------------------
# Phase 4: Discrete-event execution formalization
# ----------------------------

EVENT_FILES: Dict[str, str] = {}

EVENT_FILES["app/sim_kernel/events.py"] = """\
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Event:
    type: str
    payload: Dict[str, Any]


# This module exists to formalize events without forcing a refactor.
# Kernel can remain step-list based; events can be enabled later.
"""

def phase4_create_event_files() -> None:
    for rel, content in EVENT_FILES.items():
        write_file(REPO_ROOT / rel, content)
    log("PHASE 4 - Added events model placeholder.")


# ----------------------------
# Phase 5: Non-transitivity detection (local cycle warning)
# ----------------------------

NT_FILES: Dict[str, str] = {}

NT_FILES["app/sim_kernel/actions/matchup_graph.py"] = """\
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
"""

NT_FILES["tests/test_non_transitive_cycle_detection.py"] = """\
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
"""

def phase5_create_nt_files() -> None:
    for rel, content in NT_FILES.items():
        write_file(REPO_ROOT / rel, content)
    log("PHASE 5 - Added local matchup graph action + cycle detection test.")


# ----------------------------
# Phase 6: Scenario regression harness (kernel-simulator style)
# ----------------------------

SCENARIO_FILES: Dict[str, str] = {}

SCENARIO_FILES["tests/scenarios/non_transitive_cycle_001.json"] = """\
{
  "id": "non_transitive_cycle_001",
  "request": {"fighter_a": "A", "fighter_b": "B"},
  "config": {"scheduler": "FIFO", "seed": 7, "depth": "standard"},
  "assert": {"warnings_contains": ["non_transitive_cycle_detected"]}
}
"""

SCENARIO_FILES["tests/test_scenarios_runner.py"] = """\
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
"""

def phase6_create_scenario_files() -> None:
    for rel, content in SCENARIO_FILES.items():
        write_file(REPO_ROOT / rel, content)
    log("PHASE 6 - Added scenarios folder + scenario runner test scaffolding.")


# ----------------------------
# Master Plan: Execute scaffold + print wiring steps
# ----------------------------

def main() -> None:
    log("=== ANTIGRAVITY PLAN START ===")
    anchors = phase0_discover_anchors()

    # Create scaffolding files
    phase1_create_kernel_files()
    phase1_wire_endpoint_instructions()

    phase2_instructions()

    phase3_create_ttt_files()
    phase3_instructions()

    phase4_create_event_files()

    phase5_create_nt_files()

    phase6_create_scenario_files()

    log("\nNEXT ACTIONS (MANDATORY):")
    log("A) Wire kernel into real /simulate endpoint using actual existing functions.")
    log("B) Replace placeholder services with real services:")
    log("   - feature_extractor, mc_engine, explainer, response_mapper")
    log("   - rating_provider using TTTAdapter + history_provider")
    log("   - matchup_graph_builder (later) with a real local neighborhood builder")
    log("C) Run tests. Fix failures with minimal diffs.")
    log("D) Commit per phase with messages:")
    log("   - feat(sim-kernel): add kernel fifo + journal")
    log("   - feat(sim-kernel): wire /simulate through kernel")
    log("   - feat(sim-kernel): add budgets + priority scheduler")
    log("   - feat(ratings): add ttt adapter baseline")
    log("   - feat(matchups): add local graph + cycle warning")
    log("   - test(scenarios): add scenario runner fixtures")
    log("\n=== ANTIGRAVITY PLAN END ===")


if __name__ == "__main__":
    main()
