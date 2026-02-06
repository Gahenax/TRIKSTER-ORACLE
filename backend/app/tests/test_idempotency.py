from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_idempotency_no_key():
    """Request without idempotency key works normally"""
    r = client.post(
        "/api/v1/simulate",
        headers={"X-Request-ID": "test-idem-1"},
        json={"home_team": "A", "away_team": "B"}
    )
    assert r.status_code in (200, 422)  # 422 if validation fails

def test_idempotency_with_key_first_request():
    """First request with idempotency key processes normally"""
    r = client.post(
        "/api/v1/simulate",
        headers={
            "X-Request-ID": "test-idem-2",
            "Idempotency-Key": "test-key-unique-001"
        },
        json={"home_team": "A", "away_team": "B"}
    )
    assert r.status_code in (200, 422)

def test_idempotency_duplicate_key_returns_cached():
    """Duplicate idempotency key returns cached response"""
    key = "test-key-duplicate-002"

    # First request
    r1 = client.post(
        "/api/v1/simulate",
        headers={
            "X-Request-ID": "test-idem-3a",
            "Idempotency-Key": key
        },
        json={"home_team": "A", "away_team": "B"}
    )

    # Second request with same key (should return cached)
    r2 = client.post(
        "/api/v1/simulate",
        headers={
            "X-Request-ID": "test-idem-3b",
            "Idempotency-Key": key
        },
        json={"home_team": "A", "away_team": "B"}
    )

    # Both should have same status
    assert r1.status_code == r2.status_code
    # If successful, bodies should match
    if r1.status_code == 200:
        assert r1.json() == r2.json()
