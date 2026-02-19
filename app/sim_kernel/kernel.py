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
