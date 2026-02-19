import os
import pytest
from main import TricksterOracleApp
from core.lifecycle import EventState, LifecycleError

def test_lifecycle_bugs():
    db_path = "diag_life.db"
    ledger_path = "diag_life.jsonl"
    if os.path.exists(db_path): os.remove(db_path)
    if os.path.exists(ledger_path): os.remove(ledger_path)
    
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    ekey = "life_1"
    
    # 1. Normal path
    app.lifecycle.transition_to(ekey, EventState.PROFILE_SET)
    app.lifecycle.transition_to(ekey, EventState.SNAPSHOT_TAKEN)
    app.lifecycle.transition_to(ekey, EventState.SIMULATED)
    app.lifecycle.transition_to(ekey, EventState.LOCKED)
    
    # 2. Try to go back
    try:
        app.lifecycle.transition_to(ekey, EventState.SIMULATED)
        assert False, "Should not allow SIMULATED from LOCKED"
    except LifecycleError as e:
        print(f"Caught expected back-transition error: {e}")

    # 3. Verify rehydration restores state
    app.shutdown()
    os.remove(db_path)
    
    app2 = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    state = app2.lifecycle.get_state(ekey)
    print(f"Rehydrated state: {state}")
    assert state == EventState.LOCKED
    
    # 4. Check if we can still fail transitions after rehydration
    try:
        app2.lifecycle.transition_to(ekey, EventState.PROFILE_SET)
        assert False, "Should still fail"
    except LifecycleError:
        pass
    
    app2.shutdown()

if __name__ == "__main__":
    test_lifecycle_bugs()
