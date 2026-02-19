import json
import argparse
from sim.scenario import Scenario
from core.contract import RiskEvaluationResult

def verify_suite(fixture_path: str):
    print(f"--- TRICKSTER VERIFICATION RUNNER ---")
    print(f"Suite: {fixture_path}\n")
    
    with open(fixture_path, 'r') as f:
        suite = json.load(f)
        
    passed = 0
    failed = 0
    
    for case in suite:
        name = case["name"]
        inputs = case["inputs"]
        expected = case["expected_output"]
        
        sc = Scenario(**inputs)
        # Match n_sims from baseline
        actual = sc.evaluate(n_sims=expected["n_sims"])
        
        # 1. Validate Schema
        try:
            RiskEvaluationResult(**actual)
        except Exception as e:
            print(f"[FAIL] {name}: Schema validation failed: {e}")
            failed += 1
            continue

        # 2. Compare content (Determinism Check)
        diffs = []
        for key in ["pls", "zone", "determinism_signature"]:
            if actual[key] != expected[key]:
                diffs.append(f"{key}: expected {expected[key]}, got {actual[key]}")
        
        if diffs:
            print(f"[FAIL] {name}:")
            for d in diffs:
                print(f"  - {d}")
            failed += 1
        else:
            print(f"[PASS] {name} (Signature: {actual['determinism_signature'][:8]}...)")
            passed += 1
            
    print(f"\n--- SUMMARY ---")
    print(f"TOTAL: {len(suite)} | PASS: {passed} | FAIL: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="tests/fixtures/baselines.json")
    args = parser.parse_args()
    
    success = verify_suite(args.suite)
    exit(0 if success else 1)
