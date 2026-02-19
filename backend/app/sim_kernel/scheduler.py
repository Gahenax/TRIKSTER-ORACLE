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
