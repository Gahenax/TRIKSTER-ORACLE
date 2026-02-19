from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.db.models import Snapshot, SnapshotTypeEnum

class SnapshotManager:
    """
    Manages event snapshots (PREMATCH, LIVE, FINAL).
    Snapshots are stored in DB for auditability and simulation consistency.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_snapshot(self, event_key: str, snapshot_type: SnapshotTypeEnum, data: Dict[str, Any]) -> Snapshot:
        snapshot = Snapshot(
            event_key=event_key,
            type=snapshot_type,
            data=data,
            timestamp=datetime.utcnow()
        )
        self.db_session.add(snapshot)
        self.db_session.commit()
        return snapshot

    def get_latest_snapshot(self, event_key: str, snapshot_type: Optional[SnapshotTypeEnum] = None) -> Optional[Snapshot]:
        query = self.db_session.query(Snapshot).filter(Snapshot.event_key == event_key)
        if snapshot_type:
            query = query.filter(Snapshot.type == snapshot_type)
        
        return query.order_by(Snapshot.timestamp.desc()).first()

    def get_prematch_baseline(self, event_key: str) -> Optional[Snapshot]:
        return self.get_latest_snapshot(event_key, SnapshotTypeEnum.PREMATCH)
