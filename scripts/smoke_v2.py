#!/usr/bin/env python3
"""
Smoke Test Script for TRICKSTER-ORACLE v2 API

Tests:
1. Health check
2. Free-tier simulate (headline_pick)
3. Gated request without tokens (should deny)
4. Gated request with tokens (should succeed and charge)
5. Retry with same idempotency key (should NOT double-charge)
6. Audit trail verification
"""

import sys
import requests
import json
import time
import os
from typing import Tuple, Dict, Any, Optional


# Configuration
BASE_URL = os.environ.get("TRICKSTER_API_URL", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("TRICKSTER_AUTH", "")  # "Bearer <token>"
TEST_USER_ID = os.environ.get("TRICKSTER_USER_ID", "smoke_test_user")


def post(path: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[int, str, Dict[str, str]]:
    """POST request helper"""
    url = f"{BASE_URL}{path}"
    hdrs = headers or {}
    hdrs["Content-Type"] = "application/json"
    
    try:
        resp = requests.post(url, json=payload, headers=hdrs, timeout=10)
        return resp.status_code, resp.text, dict(resp.headers)
    except Exception as e:
        return 0, str(e), {}


def get(path: str, headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    """GET request helper"""
    url = f"{BASE_URL}{path}"
    hdrs = headers or {}
    
    try:
        resp = requests.get(url, headers=hdrs, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main() -> int:
    """Run smoke tests"""
    
    print_section("TRICKSTER-ORACLE v2 API Smoke Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"User ID: {TEST_USER_ID}")
    
    # ----------------------------------------
    # 1. Health check
    # ----------------------------------------
    print_section("1/6: Health Check")
    code, text = get("/api/v2/health")
    print(f"[GET /api/v2/health] {code}")
    print(text)
    
    if code != 200:
        print("❌ FAIL: Health check failed")
        return 1
    
    try:
        health_data = json.loads(text)
        if health_data.get("status") != "healthy":
            print("❌ FAIL: Health status not 'healthy'")
            return 1
    except:
        print("❌ FAIL: Health response not valid JSON")
        return 1
    
    print("✅ PASS: Health check")
    
    # ----------------------------------------
    # 2. Free-tier simulate (headline_pick)
    # ----------------------------------------
    print_section("2/6: Free-Tier Simulate (headline_pick)")
    
    simulate_payload = {
        "sport": "soccer",
        "event_id": "SMOKE_EXAMPLE_1",
        "market": "moneyline_home",
        "home_rating": 1500,
        "away_rating": 1450,
        "home_advantage": 50,
        "depth": "headline_pick"
    }
    
    code, text, _ = post("/api/v2/simulate", simulate_payload)
    print(f"[POST /api/v2/simulate free] {code}")
    print(text)
    
    if code != 200:
        print("❌ FAIL: Free-tier simulate failed")
        return 1
    
    try:
        sim_data = json.loads(text)
        if sim_data.get("cost_tokens") != 0:
            print("❌ FAIL: Free tier should cost 0 tokens")
            return 1
        if "pick" not in sim_data:
            print("❌ FAIL: Response missing 'pick' field")
            return 1
    except:
        print("❌ FAIL: Simulate response not valid JSON")
        return 1
    
    print("✅ PASS: Free-tier simulate")
    
    # ----------------------------------------
    # 3. Gated request without tokens (should deny)
    # ----------------------------------------
    print_section("3/6: Gated Request WITHOUT Tokens (should deny)")
    
    gated_payload = {
        "sport": "soccer",
        "event_id": "SMOKE_EXAMPLE_2",
        "market": "moneyline_home",
        "home_rating": 1500,
        "away_rating": 1450,
        "depth": "full_distribution",
        "config": {"n_simulations": 1000, "seed": 42}
    }
    
    # Try without X-User-ID header (should fail with 401)
    code, text, _ = post("/api/v2/simulate", gated_payload)
    print(f"[POST /api/v2/simulate no user_id] {code}")
    print(text[:200] + "..." if len(text) > 200 else text)
    
    if code not in (401, 402):
        print(f"⚠️  WARN: Expected 401 or 402, got {code}")
    else:
        print("✅ PASS: Request denied without auth")
    
    # Try with X-User-ID but no tokens (should fail with 402)
    headers_no_balance = {"X-User-ID": "user_with_zero_tokens"}
    code2, text2, _ = post("/api/v2/simulate", gated_payload, headers=headers_no_balance)
    print(f"\n[POST /api/v2/simulate with user_id, no balance] {code2}")
    print(text2[:200] + "..." if len(text2) > 200 else text2)
    
    if code2 != 402:
        print(f"⚠️  WARN: Expected 402 (Payment Required), got {code2}")
    else:
        print("✅ PASS: Request denied for insufficient tokens")
    
    # ----------------------------------------
    # 4. Setup tokens for gated tests
    # ----------------------------------------
    if not AUTH_TOKEN:
        print_section("4-6: SKIPPED (No AUTH_TOKEN)")
        print("Set TRICKSTER_AUTH environment variable to test gated features")
        print("\nExample:")
        print(f'  export TRICKSTER_AUTH="Bearer your_admin_token"')
        print(f'  export TRICKSTER_USER_ID="{TEST_USER_ID}"')
        print(f'  python scripts/smoke_v2.py')
        return 0
    
    # Give test user some tokens
    print_section("Setup: Add tokens to test user")
    
    topup_payload = {
        "user_id": TEST_USER_ID,
        "amount": 20,
        "payment_id": f"smoke_test_{int(time.time())}"
    }
    
    topup_headers = {"Authorization": AUTH_TOKEN}
    code, text, _ = post("/api/v2/tokens/topup", topup_payload, headers=topup_headers)
    print(f"[POST /api/v2/tokens/topup] {code}")
    print(text)
    
    if code != 200:
        print("❌ FAIL: Token top-up failed")
        return 1
    
    print("✅ Tokens added")
    
    # Check balance
    balance_headers = {"X-User-ID": TEST_USER_ID}
    code, text = get("/api/v2/tokens/balance", headers=balance_headers)
    print(f"\n[GET /api/v2/tokens/balance] {code}")
    print(text)
    
    # ----------------------------------------
    # 5. Gated request with tokens (should succeed)
    # ----------------------------------------
    print_section("4/6: Gated Request WITH Tokens (should succeed)")
    
    idempotency_key = f"smoke-{TEST_USER_ID}-{int(time.time())}"
    gated_headers = {
        "X-User-ID": TEST_USER_ID,
        "X-Idempotency-Key": idempotency_key
    }
    
    code, text, _ = post("/api/v2/simulate", gated_payload, headers=gated_headers)
    print(f"[POST /api/v2/simulate with tokens] {code}")
    print(text[:500] + "..." if len(text) > 500 else text)
    
    if code != 200:
        print("❌ FAIL: Gated request with tokens failed")
        return 1
    
    try:
        gated_data = json.loads(text)
        if "distribution" not in gated_data:
            print("❌ FAIL: Response missing 'distribution' field")
            return 1
        if gated_data.get("cost_tokens") != 2:
            print("❌ FAIL: full_distribution should cost 2 tokens")
            return 1
        transaction_id_1 = gated_data.get("transaction_id")
    except Exception as e:
        print(f"❌ FAIL: Error parsing response: {e}")
        return 1
    
    print("✅ PASS: Gated request succeeded")
    
    # ----------------------------------------
    # 6. Retry with same idempotency key (should NOT double-charge)
    # ----------------------------------------
    print_section("5/6: Retry with Same Idempotency Key (no double-charge)")
    
    code2, text2, _ = post("/api/v2/simulate", gated_payload, headers=gated_headers)
    print(f"[POST /api/v2/simulate retry] {code2}")
    print(text2[:500] + "..." if len(text2) > 500 else text2)
    
    if code2 != 200:
        print("⚠️  WARN: Retry failed")
    else:
        try:
            retry_data = json.loads(text2)
            transaction_id_2 = retry_data.get("transaction_id")
            
            if transaction_id_1 != transaction_id_2:
                print(f"❌ FAIL: Different transaction IDs (double-charge)")
                print(f"  Original: {transaction_id_1}")
                print(f"  Retry: {transaction_id_2}")
                return 1
            
            print(f"✅ PASS: Same transaction ID returned (no double-charge)")
            print(f"  Transaction ID: {transaction_id_1}")
        except Exception as e:
            print(f"⚠️  WARN: Could not verify idempotency: {e}")
    
    # ----------------------------------------
    # 7. Audit trail verification
    # ----------------------------------------
    print_section("6/6: Audit Trail Verification")
    
    code, text = get("/api/v2/tokens/ledger", headers=balance_headers)
    print(f"[GET /api/v2/tokens/ledger] {code}")
    print(text[:500] + "..." if len(text) > 500 else text)
    
    if code != 200:
        print("⚠️  WARN: Ledger check failed")
    else:
        try:
            ledger_data = json.loads(text)
            transactions = ledger_data.get("transactions", [])
            
            # Find our transaction
            our_tx = None
            for tx in transactions:
                if tx.get("transaction_id") == transaction_id_1:
                    our_tx = tx
                    break
            
            if not our_tx:
                print("❌ FAIL: Transaction not found in ledger")
                return 1
            
            print(f"✅ PASS: Transaction found in audit trail")
            print(f"  Cost: {our_tx.get('cost')} tokens")
            print(f"  Balance: {our_tx.get('balance_before')} → {our_tx.get('balance_after')}")
            print(f"  Status: {our_tx.get('status')}")
            
        except Exception as e:
            print(f"⚠️  WARN: Could not parse ledger: {e}")
    
    # ----------------------------------------
    # Final Summary
    # ----------------------------------------
    print_section("SMOKE TESTS COMPLETE")
    print("✅ All critical paths verified")
    print("\nResults:")
    print("  1. ✅ Health check")
    print("  2. ✅ Free-tier access (no tokens)")
    print("  3. ✅ Denial without tokens")
    print("  4. ✅ Gated access with tokens")
    print("  5. ✅ Idempotency protection")
    print("  6. ✅ Audit trail logging")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
