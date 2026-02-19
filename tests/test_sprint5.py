import os
import json
import pytest
import stat
from main import TricksterOracleApp
from core.lifecycle import EventState, LifecycleError
from core.ledger.manager import LedgerSchemaError

@pytest.fixture
def clean_app(tmp_path):
    db_path = str(tmp_path / "test.db")
    ledger_path = str(tmp_path / "test.jsonl")
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    yield app, db_path, ledger_path
    app.shutdown()

def test_ledger_schema_validation_rejects_bad_entries(clean_app):
    app, _, _ = clean_app
    with pytest.raises(LedgerSchemaError):
        # Missing required fields like entry_id, ts, etc.
        app.ledger.validate_entry({"action_type": "TEST"})

def test_event_lifecycle_enforcement(clean_app):
    app, _, _ = clean_app
    ekey = "event_123"
    
    # Valid: CREATED -> PROFILE_SET
    app.lifecycle.transition_to(ekey, EventState.PROFILE_SET)
    assert app.lifecycle.get_state(ekey) == EventState.PROFILE_SET
    
    # Invalid: PROFILE_SET -> SIMULATED (skips SNAPSHOT_TAKEN)
    with pytest.raises(LifecycleError):
        app.lifecycle.transition_to(ekey, EventState.SIMULATED)

def test_profile_immutability_enforced(clean_app):
    app, _, _ = clean_app
    ekey = "event_immut"
    
    app.event_manager.set_risk_profile(ekey, "NEUTRAL")
    
    # Attempting to change should raise ValueError
    with pytest.raises(ValueError, match="already set"):
        app.event_manager.set_risk_profile(ekey, "RISKY")

def test_db_rehydration_matches_ledger(tmp_path):
    db_path = str(tmp_path / "base.db")
    ledger_path = str(tmp_path / "base.jsonl")
    
    # 1. Create data in original app
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    app.event_manager.set_risk_profile("key_1", "CONSERVATIVE")
    app.shutdown()
    
    # 2. Delete DB
    os.remove(db_path)
    assert not os.path.exists(db_path)
    
    # 3. New app should rehydrate
    app2 = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    # Check if profile was rehydrated in DB
    from core.db.models import EventProfile
    profile = app2.db_session.query(EventProfile).filter_by(event_key="key_1").first()
    assert profile is not None
    assert profile.profile == "CONSERVATIVE"
    app2.shutdown()

def test_fail_closed_on_ledger_write_error(tmp_path):
    db_path = str(tmp_path / "fail.db")
    ledger_path = str(tmp_path / "fail.jsonl")
    
    # Initial setup
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    # Ensure file exists before chmod
    app.ledger.log_event("INIT", "global", {"msg": "start"})
    app.shutdown()
    
    # Make ledger read-only to simulate write failure
    os.chmod(ledger_path, stat.S_IREAD)
    
    app2 = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    with pytest.raises(RuntimeError, match="Fail-closed triggered"):
        # This should fail because it's read-only
        app2.ledger.log_event("TEST", "ekey", {"msg": "should fail"})
    
    app2.shutdown()
    # Restore permissions for cleanup
    os.chmod(ledger_path, stat.S_IWRITE | stat.S_IREAD)

def test_partial_line_detection(tmp_path):
    db_path = str(tmp_path / "corrupt.db")
    ledger_path = str(tmp_path / "corrupt.jsonl")
    
    with open(ledger_path, 'w') as f:
        f.write('{"valid": "line"}\n')
        f.write('{"partial": "line"') # No newline, incomplete JSON
        
    with pytest.raises(RuntimeError, match="ends with a partial line"):
        TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
