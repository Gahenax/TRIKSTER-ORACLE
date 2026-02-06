#!/usr/bin/env python3
"""
Runtime Test Suite - TRICKSTER-ORACLE
Tests all endpoints locally before deployment
"""
import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

def test_health():
    """Test /health endpoint"""
    print("\n[TEST] GET /health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Headers: X-Request-ID: {response.headers.get('X-Request-ID', 'MISSING')}")
        print(f"Headers: X-Process-Time: {response.headers.get('X-Process-Time', 'MISSING')}ms")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        
        # Assertions
        assert response.status_code == 200, "Health check should return 200"
        assert "X-Request-ID" in response.headers, "X-Request-ID header missing"
        assert response.json()["status"] == "healthy", "Status should be healthy"
        
        print("[PASS]")
        return True
    except Exception as e:
        print(f"[FAIL]: {e}")
        return False


def test_ready():
    """Test /ready endpoint"""
    print("\n[TEST] GET /ready")
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        
        # Assertions
        assert response.status_code == 200, "Ready check should return 200"
        assert response.json()["ready"] == True, "Should be ready"
        
        print("[PASS]")
        return True
    except Exception as e:
        print(f"[FAIL]: {e}")
        return False


def test_version():
    """Test /version endpoint"""
    print("\n[TEST] GET /version")
    try:
        response = requests.get(f"{BASE_URL}/version", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Body: {json.dumps(data, indent=2)}")
        
        # Assertions
        assert response.status_code == 200, "Version should return 200"
        assert "build_commit" in data, "build_commit should be present"
        assert "environment" in data, "environment should be present"
        
        print("[PASS]")
        return True
    except Exception as e:
        print(f"[FAIL]: {e}")
        return False


def test_request_id_preservation():
    """Test that X-Request-ID header is preserved"""
    print("\n[TEST] Request-ID Preservation")
    custom_id = "test-request-12345"
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            headers={"X-Request-ID": custom_id},
            timeout=5
        )
        returned_id = response.headers.get("X-Request-ID")
        print(f"Sent: {custom_id}")
        print(f"Received: {returned_id}")
        
        # Assertion
        assert returned_id == custom_id, f"Request ID should be preserved: sent={custom_id}, got={returned_id}"
        
        print("[PASS]")
        return True
    except Exception as e:
        print(f"[FAIL]: {e}")
        return False


def test_root():
    """Test / root endpoint"""
    print("\n[TEST] GET /")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, "Root should return 200"
        
        print("[PASS]")
        return True
    except Exception as e:
        print(f"[FAIL]: {e}")
        return False


def main():
    print("=" * 60)
    print("RUNTIME TEST SUITE - TRICKSTER-ORACLE")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for server
    print("\n[*] Waiting for server to be ready...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("[*] Server is ready!")
            break
        except:
            time.sleep(1)
            print(f"[*] Attempt {i+1}/10...")
    else:
        print("[X] Server not responding after 10 seconds")
        return 1
    
    # Run tests
    results = []
    tests = [
        ("Health Endpoint", test_health),
        ("Ready Endpoint", test_ready),
        ("Version Endpoint", test_version),
        ("Request-ID Preservation", test_request_id_preservation),
        ("Root Endpoint", test_root),
    ]
    
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print()
    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED - Ready for deployment!")
        return 0
    else:
        print(f"\n[ERROR] {failed} TEST(S) FAILED - Fix before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
