from sqlalchemy.orm import Session
from core.db.models import Event, EventProfile, RiskProfileEnum
from core.ledger.manager import LedgerManager
from core.utils import generate_event_key
from datetime import datetime, timezone

class EventManager:
    """
    Handles event creation and risk profile enforcement.
    """
    
    def __init__(self, db_session: Session, ledger: LedgerManager):
        self.db_session = db_session
        self.ledger = ledger

    def set_risk_profile(self, event_key: str, profile: RiskProfileEnum):
        """
        Sets the risk profile for an EventKey.
        Enforces "One profile per EventKey" rule.
        """
        # Check if already exists
        existing = self.db_session.query(EventProfile).filter(EventProfile.event_key == event_key).first()
        
        if existing:
            if existing.profile == profile:
                return # Already set to this
            
            # ATTEMPT TO CHANGE DETECTED
            self.ledger.log_event(
                action_type="PROVIDER_ERROR", 
                event_key=event_key,
                payload={
                    "msg": "Blocked attempt to change risk profile",
                    "existing": existing.profile,
                    "attempted": profile
                },
                status="FAIL"
            )
            raise ValueError(f"CRITICAL: Risk profile for event {event_key} is already set and cannot be changed.")

        # Create new profile
        new_profile = EventProfile(
            event_key=event_key,
            profile=profile,
            set_at=datetime.now(timezone.utc)
        )
        self.db_session.add(new_profile)
        
        # Log to ledger
        self.ledger.log_event(
            action_type="EVENT_PROFILE_SET", 
            event_key=event_key,
            payload={"profile": profile}
        )
        
        self.db_session.commit()
