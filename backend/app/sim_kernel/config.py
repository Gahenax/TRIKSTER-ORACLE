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
