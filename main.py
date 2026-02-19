import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db.models import Base, LedgerEntry, Sport, League, Entity, Event, EventProfile, Snapshot, Wallet
from core.ledger.manager import LedgerManager
from core.event_manager import EventManager
from core.tokens import TokenWallet
from core.lifecycle import LifecycleManager, EventState
from store.cache_manager import CacheManager
from store.snapshot_manager import SnapshotManager

class TricksterOracleApp:
    def __init__(self, db_path="oracle.db", ledger_path="ledger.jsonl", force_rehydrate=False):
        self.db_path = db_path
        self.ledger_path = ledger_path
        
        # 1. DB initialization
        db_exists = os.path.exists(db_path)
        if force_rehydrate and db_exists:
            try:
                os.remove(db_path)
                db_exists = False
            except PermissionError:
                pass # Will try to clear later or overwrite

        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # 2. Ledger foundation
        self.ledger = LedgerManager(ledger_path, self.db_session)
        
        # 3. Core systems
        self.lifecycle = LifecycleManager(self.ledger)
        self.event_manager = EventManager(self.db_session, self.ledger)
        self.tokens = TokenWallet(self.db_session, self.ledger)
        
        # 4. Storage
        self.cache = CacheManager("cache")
        self.snapshots = SnapshotManager(self.db_session)

        # 5. Handle empty/new DB rehydration if ledger exists
        if not db_exists and os.path.exists(ledger_path):
            self.rehydrate_db_from_ledger()

    def rehydrate_db_from_ledger(self):
        """
        Replays ledger.jsonl to rebuild the L1 (DB) cache.
        Authority: Ledger.
        """
        if not os.path.exists(self.ledger_path):
            return

        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    self._replay_event(entry)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"CRITICAL: Ledger corruption detected at line {line_no}. Authority is compromised. Error: {e}")
        
        self.db_session.commit()

    def _replay_event(self, entry: dict):
        """Internal logic to project a ledger entry into the DB."""
        action = entry["action_type"]
        data = entry["payload"]
        event_key = entry["event_key"]

        if action == "EVENT_PROFILE_SET":
            profile = EventProfile(
                event_key=event_key,
                profile=data["profile"]
            )
            self.db_session.merge(profile)
        
        elif action == "STATE_TRANSITION":
            self.lifecycle.set_initial_state(event_key, EventState(data["to"]))

        elif action == "SNAPSHOT_CREATED":
            snap = Snapshot(
                event_key=event_key,
                type=data["type"],
                data=data["data"]
            )
            self.db_session.merge(snap)

        db_entry = LedgerEntry(event_type=action, data=entry)
        self.db_session.add(db_entry)

    def shutdown(self):
        """Cleanly close DB session and engine."""
        if self.db_session:
            self.db_session.close()
        if self.engine:
            self.engine.dispose()
