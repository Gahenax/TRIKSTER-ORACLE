# -*- coding: utf-8 -*-
"""
Quick smoke test for local API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
USER_ID = "smoke_test_user"

print("\n" + "="*70)
print("  QUICK SMOKE TEST - TRICKSTER v2 API")
print("="*70)

# Test 1: Health
print("\n[1/5] Health Check...")
resp = requests.get(f"{BASE_URL}/api/v2/health")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")
assert resp.status_code == 200
assert resp.json()["status"] == "healthy"
print("[PASS] Health check OK")

# Test 2: Free tier
print("\n[2/5] Free-Tier Simulate...")
payload = {
    "sport": "soccer",
    "event_id": "test_free",
    "home_rating": 1500,
    "away_rating": 1450,
    "depth": "headline_pick"
}
resp = requests.post(f"{BASE_URL}/api/v2/simulate", json=payload)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Cost: {data.get('cost_tokens')} tokens")
print(f"Pick: {data.get('pick')}")
assert resp.status_code == 200
assert data["cost_tokens"] == 0
print("[PASS] Free tier OK")

# Test 3: Check balance
print("\n[3/5] Check Token Balance...")
resp = requests.get(
    f"{BASE_URL}/api/v2/tokens/balance",
    headers={"X-User-ID": USER_ID}
)
print(f"Status: {resp.status_code}")
balance_data = resp.json()
print(f"Balance: {balance_data}")
initial_balance = balance_data["balance"]
print(f"[PASS] Balance: {initial_balance} tokens")

# Test 4: Gated request (full_distribution)
print("\n[4/5] Gated Request (Full Distribution - 2 tokens)...")
payload_gated = {
    "sport": "soccer",
    "event_id": "test_gated",
    "home_rating": 1600,
    "away_rating": 1400,
    "depth": "full_distribution",
    "config": {"n_simulations": 1000, "seed": 42}
}
idempotency_key = f"test_{int(time.time())}"
headers = {
    "X-User-ID": USER_ID,
    "X-Idempotency-Key": idempotency_key
}
resp = requests.post(f"{BASE_URL}/api/v2/simulate", json=payload_gated, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    gated_data = resp.json()
    print(f"Cost: {gated_data.get('cost_tokens')} tokens")
    print(f"Transaction ID: {gated_data.get('transaction_id')}")
    print(f"Has distribution: {'distribution' in gated_data}")
    print(f"Has uncertainty: {'uncertainty' in gated_data}")
    assert gated_data["cost_tokens"] == 2
    tx_id_1 = gated_data["transaction_id"]
    print("[PASS] Gated request OK")
else:
    print(f"ERROR: {resp.text}")
    raise Exception("Gated request failed")

# Test 5: Idempotency (retry same request)
print("\n[5/5] Idempotency Test (same request again)...")
resp2 = requests.post(f"{BASE_URL}/api/v2/simulate", json=payload_gated, headers=headers)
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    retry_data = resp2.json()
    tx_id_2 = retry_data["transaction_id"]
    print(f"  TX 1: {tx_id_1}")
    print(f"  TX 2: {tx_id_2}")
    assert tx_id_1 == tx_id_2, "Transaction IDs should match"
    print("[PASS] Idempotency OK - same transaction returned")
else:
    print(f"ERROR: {resp2.text}")

# Final balance check
print("\n[FINAL] Balance Check...")
resp = requests.get(
    f"{BASE_URL}/api/v2/tokens/balance",
    headers={"X-User-ID": USER_ID}
)
final_balance = resp.json()["balance"]
print(f"Initial: {initial_balance} tokens")
print(f"Final: {final_balance} tokens")
print(f"Consumed: {initial_balance - final_balance} tokens (expected: 2)")
assert initial_balance - final_balance == 2, "Should have consumed exactly 2 tokens"
print("[PASS] Balance check OK")

# Summary
print("\n" + "="*70)
print("  ALL TESTS PASSED")
print("="*70)
print(f"""
Summary:
  [PASS] Health check
  [PASS] Free-tier access (0 tokens)
  [PASS] Token balance check
  [PASS] Gated access (2 tokens consumed)
  [PASS] Idempotency protection (no double-charge)
  
Backend v2 API is FULLY FUNCTIONAL!
""")
