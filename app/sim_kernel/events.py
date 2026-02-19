from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Event:
    type: str
    payload: Dict[str, Any]


# This module exists to formalize events without forcing a refactor.
# Kernel can remain step-list based; events can be enabled later.
