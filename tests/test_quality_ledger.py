import os
import concurrent.futures
import pytest
from main import TricksterOracleApp

def test_ledger_concurrency_stress(tmp_path):
    """
    Task Q1.2: Stress test the Ledger under high concurrent load.
    Ensures that multiple threads writing to the same ledger file 
    do not cause line corruption or DB deadlocks.
    """
    db_path = str(tmp_path / "stress.db")
    ledger_path = str(tmp_path / "stress.jsonl")
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    
    NUM_THREADS = 10
    WRITES_PER_THREAD = 50
    
    def worker(tid):
        # We need a local session for each thread if we want true DB concurrency,
        # but here we are testing the LedgerManager's file-locking/append logic.
        # Since our LedgerManager uses a single session from app, we'll see 
        # how SQLAlchemy handles the mirror side.
        for i in range(WRITES_PER_THREAD):
            app.ledger.log_event(
                action_type="STRESS_TEST",
                event_key=f"thread_{tid}",
                payload={"iter": i, "data": "x" * 100},
                token_delta=0
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(worker, i) for i in range(NUM_THREADS)]
        concurrent.futures.wait(futures)

    app.shutdown()
    
    # 1. Verify JSONL line count
    with open(ledger_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Expect (NUM_THREADS * WRITES_PER_THREAD) + some possible init events
        # Our app might log EVENT_PROFILE_SET or similar if called, but worker only does STRESS_TEST.
        assert len(lines) >= (NUM_THREADS * WRITES_PER_THREAD)
        
    # 2. Verify all lines are valid JSON (No interleaving)
    import json
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            pytest.fail(f"Interleaved/Corrupted line found in ledger: {line[:50]}... Error: {e}")

def test_ledger_atomic_append_resilience(tmp_path):
    """Verify that file remains valid even with large payloads."""
    db_path = str(tmp_path / "large.db")
    ledger_path = str(tmp_path / "large.jsonl")
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    
    # Large payload (100KB)
    large_payload = {"data": "A" * 100000}
    app.ledger.log_event("LARGE_WRITE", "global", large_payload)
    
    app.shutdown()
    
    # Check if last char is newline
    with open(ledger_path, 'rb') as f:
        f.seek(-1, os.SEEK_END)
        assert f.read(1) == b'\n'
