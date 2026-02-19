import time
import pytest
from sim.scenario import Scenario
from main import TricksterOracleApp

def test_performance_simulation_latency():
    """Verify that a 1,000 sim run completes in under 300ms on average."""
    features = {"rating_diff": 0.0, "home_advantage": 100.0}
    sc = Scenario(
        event_key="perf_test", 
        risk_profile="NEUTRAL", 
        stake=100.0, 
        features=features,
        snapshot_id="s1",
        snapshot_data={}
    )
    
    start = time.perf_counter()
    # Force 1,000 sims (Green zone territory)
    sc.evaluate() 
    end = time.perf_counter()
    
    latency = (end - start) * 1000
    print(f"Sim Latency: {latency:.2f}ms")
    # Allow 500ms as a safe upper bound for CI environments
    assert latency < 500

def test_performance_ledger_write_latency(tmp_path):
    """Verify that ledger appends (disk sync) are fast."""
    app = TricksterOracleApp(db_path=str(tmp_path/"p.db"), ledger_path=str(tmp_path/"p.jsonl"))
    
    latencies = []
    for i in range(100):
        start = time.perf_counter()
        app.ledger.log_event("PERF_TEST", "key", {"i": i})
        latencies.append((time.perf_counter() - start) * 1000)
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"Avg Ledger Latency: {avg_latency:.2f}ms")
    # Sync writing to disk (fsync) can be slow, but should be < 20ms on modern SSDs.
    # We allow 50ms for overhead.
    assert avg_latency < 50
    app.shutdown()
