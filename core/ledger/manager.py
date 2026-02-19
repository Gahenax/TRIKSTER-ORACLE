import json
import os
import uuid
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.db.models import LedgerEntry

class LedgerSchemaError(Exception):
    """Raised when an entry does not match the strict ledger schema."""
    pass

class LedgerManager:
    """
    Append-only JSONL ledger with strict schema and DB mirroring.
    Fail-closed: Operation fails if ledger write cannot be guaranteed.
    """
    
    SCHEMA_VERSION = 1
    REQUIRED_FIELDS = {
        "entry_id", "ts", "action_type", "event_key", 
        "status", "payload_hash", "token_delta", "actor", "schema_version"
    }

    def __init__(self, log_path: str, db_session: Session):
        self.log_path = log_path
        self.db_session = db_session
        self._lock = threading.Lock()
        
        # Ensure directory exists if path has one
        dir_name = os.path.dirname(log_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        # Verify ledger integrity on startup
        self._verify_integrity()

    def _verify_integrity(self):
        """Checks for partial lines or corruption in the ledger file."""
        if not os.path.exists(self.log_path):
            return
            
        try:
            with open(self.log_path, 'rb') as f:
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    return
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b'\n':
                    raise RuntimeError(f"CORRUPTION: Ledger file {self.log_path} ends with a partial line. Manual audit required.")
        except IOError as e:
            raise RuntimeError(f"CRITICAL: Cannot access ledger file for integrity check. {e}")

    def validate_entry(self, entry: Dict[str, Any]):
        """Enforces schema validation."""
        missing = self.REQUIRED_FIELDS - set(entry.keys())
        if missing:
            raise LedgerSchemaError(f"Missing required fields: {missing}")
            
        if not isinstance(entry["token_delta"], int):
            raise LedgerSchemaError("token_delta must be an integer")

    def log_event(self, action_type: str, event_key: str, payload: Dict[str, Any], 
                  snapshot_id: str = "N/A", token_delta: int = 0, actor: str = "system", 
                  status: str = "SUCCESS"):
        """
        Logs a strict event to both JSONL file and database.
        Thread-safe locked implementation.
        """
        
        payload_json = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        
        entry = {
            "entry_id": uuid.uuid4().hex,
            "ts": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "event_key": event_key,
            "snapshot_id": snapshot_id,
            "status": status,
            "payload_hash": payload_hash,
            "payload": payload,
            "token_delta": token_delta,
            "actor": actor,
            "schema_version": self.SCHEMA_VERSION
        }
        
        # Validate before write
        self.validate_entry(entry)
        
        with self._lock:
            # 1. Atomic-like append to JSONL
            try:
                line = json.dumps(entry) + '\n'
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno()) 
            except Exception as e:
                raise RuntimeError(f"CRITICAL: Fail-closed triggered. Ledger write failed: {e}")

            # 2. Mirror to DB
            try:
                db_entry = LedgerEntry(
                    event_type=action_type,
                    data=entry
                )
                self.db_session.add(db_entry)
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback() # Important for threads
                raise RuntimeError(f"CRITICAL: Database mirror failed. Divergence detected. {e}")

        return entry["entry_id"]
