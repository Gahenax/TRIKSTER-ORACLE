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
