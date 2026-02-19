from enum import Enum
from typing import Dict, List, Optional
from core.ledger.manager import LedgerManager

class EventState(str, Enum):
    CREATED = "CREATED"
    PROFILE_SET = "PROFILE_SET"
    SNAPSHOT_TAKEN = "SNAPSHOT_TAKEN"
    SIMULATED = "SIMULATED"
    LOCKED = "LOCKED"

class LifecycleError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class LifecycleManager:
    """
    Enforces event lifecycle transitions:
    CREATED -> PROFILE_SET -> SNAPSHOT_TAKEN -> SIMULATED -> LOCKED
    """
    
    TRANSITIONS = {
        EventState.CREATED: [EventState.PROFILE_SET],
        EventState.PROFILE_SET: [EventState.SNAPSHOT_TAKEN],
        EventState.SNAPSHOT_TAKEN: [EventState.SIMULATED],
        EventState.SIMULATED: [EventState.SIMULATED, EventState.LOCKED], # Can simulate multiple times unless locked
        EventState.LOCKED: [] # Terminal state
    }

    def __init__(self, ledger: LedgerManager):
        self.ledger = ledger
        # In-memory session state for fast checks, 
        # but source of truth is the ledger/DB.
        self._states: Dict[str, EventState] = {}

    def get_state(self, event_key: str) -> EventState:
        # For v1, we check the internal cache or could query DB
        return self._states.get(event_key, EventState.CREATED)

    def transition_to(self, event_key: str, new_state: EventState, actor: str = "system"):
        current_state = self.get_state(event_key)
        
        if new_state not in self.TRANSITIONS.get(current_state, []):
            msg = f"Invalid transition: {current_state} -> {new_state} for event {event_key}"
            self.ledger.log_event(
                action_type="LIFECYCLE_ERROR",
                event_key=event_key,
                payload={"error": msg, "current": current_state, "attempted": new_state},
                actor=actor,
                status="FAIL"
            )
            raise LifecycleError(msg)

        # Log valid transition
        self.ledger.log_event(
            action_type="STATE_TRANSITION",
            event_key=event_key,
            payload={"from": current_state, "to": new_state},
            actor=actor,
            status="SUCCESS"
        )
        
        self._states[event_key] = new_state
        return True

    def set_initial_state(self, event_key: str, state: EventState = EventState.CREATED):
        """Used during rehydration or first appearance."""
        self._states[event_key] = state
