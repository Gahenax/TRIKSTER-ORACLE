# 🌐 Trickster Oracle API Documentation

**Version**: 0.1.0  
**Base URL**: `http://localhost:8000`  
**Production**: `https://tricksteranalytics.gahenaxaisolutions.com/api`

---

## 📋 Endpoints

### **Core Simulation**

#### `POST /api/v1/simulate`

Run Monte Carlo simulation for a sports event.

**Request Body**:
```json
{
  "event": {
    "event_id": "optional-id",
    "home_team": "Barcelona",
    "away_team": "Real Madrid",
    "home_rating": 2100,
    "away_rating": 2050,
    "home_advantage": 100,
    "sport": "football"
  },
  "config": {
    "n_simulations": 1000,
    "seed": 42
  }
}
```

**Response** (200 OK):
```json
{
  "event": { /* echo of input */ },
  "config": { /* echo of input */ },
  "prob_home": 0.542,
  "prob_draw": 0.231,
  "prob_away": 0.227,
  "distribution": {
    "bins": [0.0, 0.05, 0.1, ..., 1.0],
    "frequencies": [0, 1, 5, 12, ...]
  },
  "confidence_intervals": {
    "95": {"lower": 0.385, "upper": 0.698},
    "99": {"lower": 0.312, "upper": 0.771}
  },
  "risk": {
    "score": 52.4,
    "band": "MEDIUM",
    "rationale": "Moderate uncertainty detected..."
  },
  "explanation": {
    "summary": "Analysis shows Team A has a 54% probability...",
    "scenarios": [
      {
        "name": "Most Probable",
        "probability": 0.542,
        "description": "Home team victory based on..."
      }
    ],
    "caveats": [
      "Statistical estimates contain inherent uncertainty...",
      "Model assumptions: ELO-based ratings, logistic distribution..."
    ],
    "sensitivity": [
      {
        "factor_name": "Home Advantage +50",
        "delta_probability": 0.08,
        "impact_level": "MEDIUM"
      }
    ]
  },
  "model_version": "0.1.0",
  "execution_time_ms": 12.3,
  "cache_hit": false
}
```

**Parameters**:

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `event.home_team` | string | Yes | - | min 2 chars | Home team name |
| `event.away_team` | string | Yes | - | min 2 chars | Away team name |
| `event.home_rating` | float | Yes | - | 0-3000 | Home team ELO rating |
| `event.away_rating` | float | Yes | - | 0-3000 | Away team ELO rating |
| `event.home_advantage` | float | No | 100 | 0-300 | Home field advantage |
| `event.sport` | string | No | "football" | - | Sport type |
| `config.n_simulations` | int | No | 1000 | 100-10000 | Number of simulations |
| `config.seed` | int | No | null | - | Random seed (for reproducibility) |

**Error Responses**:

- `400 Bad Request` - Invalid input (e.g., negative ratings)
- `422 Unprocessable Entity` - Validation error (Pydantic)
- `500 Internal Server Error` - Simulation failure

---

### **Cache Management**

#### `GET /api/v1/cache/stats`

Get cache statistics.

**Response**:
```json
{
  "total_entries": 15,
  "active_entries": 12,
  "expired_entries": 3,
  "cache_ttl_seconds": 300
}
```

#### `DELETE /api/v1/cache/clear`

Clear all cached results.

**Response**:
```json
{
  "status": "success",
  "message": "Cache cleared"
}
```

---

### **Health & Info**

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "trickster-oracle-api",
  "version": "0.1.0"
}
```

#### `GET /version`

Get API version and configuration.

**Response**:
```json
{
  "version": "0.1.0",
  "api_name": "Trickster Oracle",
  "mode": "demo",
  "max_simulations_demo": 1000,
  "disclaimer": "Educational analytics platform. Not for gambling predictions."
}
```

---

## 🔒 CORS Configuration

**Allowed Origins**: `*` (development)  
**Production**: Restrict to `https://tricksteranalytics.gahenaxaisolutions.com`

**Allowed Methods**: GET, POST, DELETE  
**Allowed Headers**: All

---

## 📦 Caching

**Strategy**: In-memory cache with TTL  
**TTL**: 5 minutes (300 seconds)  
**Key**: SHA256 hash of `(event + config)`

**Cache Hit Conditions**:
- Exact same event parameters (excluding `event_id`)
- Same `n_simulations`
- Same `seed` (or both null)

**Cache Invalidation**:
- Automatic: After TTL expires
- Manual: `DELETE /api/v1/cache/clear`

---

## 🚀 Performance

| n_simulations | Typical Response Time | Max (Demo) |
|---------------|----------------------|------------|
| 100 | ~5-10 ms | - |
| 1000 | ~10-20 ms | ✅ Recommended |
| 10000 | ~100-200 ms | ✅ Max allowed |

**Note**: Cached requests return in <2ms.

---

## 🧪 Testing

### **Using curl**:

```bash
# Basic simulation
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "home_team": "Team A",
      "away_team": "Team B",
      "home_rating": 1500,
      "away_rating": 1500
    }
  }'

# With config
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "home_team": "Barcelona",
      "away_team": "Real Madrid",
      "home_rating": 2100,
      "away_rating": 2050
    },
    "config": {
      "n_simulations": 5000,
      "seed": 42
    }
  }'

# Cache stats
curl http://localhost:8000/api/v1/cache/stats

# Clear cache
curl -X DELETE http://localhost:8000/api/v1/cache/clear
```

### **Using Python**:

```python
import requests

# Simulate
response = requests.post(
    "http://localhost:8000/api/v1/simulate",
    json={
        "event": {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_rating": 1500,
            "away_rating": 1500
        },
        "config": {
            "n_simulations": 1000,
            "seed": 42
        }
    }
)

result = response.json()
print(f"Home Win Probability: {result['prob_home']:.1%}")
print(f"Risk: {result['risk']['band']} ({result['risk']['score']:.1f})")
```

---

## 📚 Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚠️ Rate Limiting (FASE 5 - Not Implemented Yet)

**Demo Mode**:
- 5 requests per day per IP
- LocalStorage tracking
- Resets at UTC midnight

---

## 🔐 Authentication (Future)

Not required in demo mode. Future versions may include:
- API keys for increased limits
- OAuth for premium features

---

## 🎓 Educational Disclaimer

**This API is for educational purposes only.**

- NOT for gambling or wagering
- NOT financial advice
- Probabilities are statistical estimates
- Results should not be used for betting decisions

All terminology follows strict anti-gambling guidelines (see GLOSSARY.md).
