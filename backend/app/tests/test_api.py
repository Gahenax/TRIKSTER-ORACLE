from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_version_endpoint():
    """Test version endpoint"""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["mode"] == "demo"
    assert "disclaimer" in data


def test_simulate_endpoint_basic():
    """Test basic simulation endpoint"""
    payload = {
        "event": {
            "event_id": "test_1",
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1500,
            "away_rating": 1500,
            "home_advantage": 100,
            "sport": "football"
        },
        "config": {
            "n_simulations": 100,
            "seed": 42
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check core fields
    assert "prob_home" in data
    assert "prob_draw" in data
    assert "prob_away" in data
    assert "risk" in data
    assert "explanation" in data
    assert "execution_time_ms" in data
    
    # Validate probabilities sum to 1
    total_prob = data["prob_home"] + data["prob_draw"] + data["prob_away"]
    assert abs(total_prob - 1.0) < 0.01


def test_simulate_endpoint_with_default_config():
    """Test simulation with default config (no config provided)"""
    payload = {
        "event": {
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "home_rating": 2100,
            "away_rating": 2050,
            "home_advantage": 100,
            "sport": "football"
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["config"]["n_simulations"] == 1000  # Default


def test_simulate_caching():
    """Test that caching works (same input returns cached result)"""
    payload = {
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1600,
            "away_rating": 1500,
            "home_advantage": 100,
            "sport": "football"
        },
        "config": {
            "n_simulations": 500,
            "seed": 123
        }
    }
    
    # First request
    response1 = client.post("/api/v1/simulate", json=payload)
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["cache_hit"] is False
    
    # Second request (should be cached)
    response2 = client.post("/api/v1/simulate", json=payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["cache_hit"] is True
    
    # Results should be identical
    assert data1["prob_home"] == data2["prob_home"]


def test_cache_stats_endpoint():
    """Test cache statistics endpoint"""
    response = client.get("/api/v1/cache/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_entries" in data
    assert "active_entries" in data
    assert "cache_ttl_seconds" in data


def test_clear_cache_endpoint():
    """Test cache clearing endpoint"""
    response = client.delete("/api/v1/cache/clear")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"


def test_simulate_invalid_rating():
    """Test validation error for invalid rating"""
    payload = {
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 5000,  # Invalid (> 3000)
            "away_rating": 1500,
            "home_advantage": 100,
            "sport": "football"
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_simulate_invalid_n_simulations():
    """Test validation error for invalid n_simulations"""
    payload = {
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1500,
            "away_rating": 1500,
            "home_advantage": 100,
            "sport": "football"
        },
        "config": {
            "n_simulations": 50000  # Invalid (> 10000)
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_risk_assessment_included():
    """Test that risk assessment is included and has correct structure"""
    payload = {
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1500,
            "away_rating": 1500,
            "home_advantage": 0,
            "sport": "football"
        },
        "config": {
            "n_simulations": 1000,
            "seed": 42
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    risk = data["risk"]
    
    assert "score" in risk
    assert "band" in risk
    assert "rationale" in risk
    assert risk["band"] in ["LOW", "MEDIUM", "HIGH"]
    assert 0 <= risk["score"] <= 100


def test_explanation_included():
    """Test that explanation is included and compliant"""
    payload = {
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 2000,
            "away_rating": 1800,
            "home_advantage": 100,
            "sport": "football"
        },
        "config": {
            "n_simulations": 1000,
            "seed": 99
        }
    }
    
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    explanation = data["explanation"]
    
    assert "summary" in explanation
    assert "scenarios" in explanation
    assert "caveats" in explanation
    
    # Check no gambling terms in summary
    forbidden = ["bet", "pick", "guaranteed", "sure thing", "profit"]
    summary_lower = explanation["summary"].lower()
    for term in forbidden:
        assert term not in summary_lower
