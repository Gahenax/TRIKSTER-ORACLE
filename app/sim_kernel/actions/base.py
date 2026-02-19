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
