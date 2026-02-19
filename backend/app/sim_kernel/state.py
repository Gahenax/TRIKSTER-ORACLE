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
