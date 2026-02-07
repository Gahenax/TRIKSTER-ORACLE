# TRICKSTER-ORACLE API v2 Contract

**Version**: 2.0.0  
**Base URL**: `/api/v2`  
**Status**: Production-ready (M1-M3 complete)  
**Backwards Compatibility**: v1 endpoints unchanged

---

## 🎯 Core Principle

**"Tokens buy depth (analysis, scenarios, export), NOT 'winning picks'"**

All v2 endpoints follow this educational framing:
- Free tier: Basic analysis always available
- Token tiers: Unlock deeper statistical analysis
- No gambling-forward language
- Transparent uncertainty quantification

---

## 📡 Endpoints

### 1. POST `/api/v2/simulate`

**Purpose**: Generate complete distribution analysis for an event.

**Authentication**: Optional (free tier doesn't require tokens)

**Request Body**:
```json
{
  "sport": "soccer",
  "event_id": "event_123",
  "market": "moneyline_home",
  "home_team": "Team A",
  "away_team": "Team B",
  "home_rating": 1500,
  "away_rating": 1450,
  "home_advantage": 50,
  "depth": "headline_pick",  // or "full_distribution", "scenario_extremes", etc.
  "config": {
    "n_simulations": 1000,
    "ci_level": 0.95,
    "seed": 42  // optional for deterministic results
  }
}
```

**Request Headers** (for gated depths):
```
Authorization: Bearer <your_token>
X-Idempotency-Key: <unique_request_id>  // optional but recommended
X-User-ID: <user_id>  // required for token gating
```

**Response (depth="headline_pick", FREE)**:
```json
{
  "sport": "soccer",
  "event_id": "event_123",
  "market": "moneyline_home",
  "model_version": "v2.0",
  "pick": {
    "predicted_outcome": "home",
    "confidence": "moderate",
    "median_probability": 0.58
  },
  "cost_tokens": 0,
  "notes": "Headline pick is always free for educational access"
}
```

**Response (depth="full_distribution", 2 tokens)**:
```json
{
  "sport": "soccer",
  "event_id": "event_123",
  "market": "moneyline_home",
  "model_version": "v2.0",
  "n_sims": 1000,
  "ci_level": 0.95,
  "seed": 42,
  
  "percentiles": {
    "p5": 0.42,
    "p25": 0.52,
    "p50": 0.58,
    "p75": 0.64,
    "p95": 0.74
  },
  
  "mean": 0.58,
  "stdev": 0.08,
  "skew": 0.12,
  "kurtosis": -0.05,
  
  "scenarios": [
    {
      "scenario_type": "conservative",
      "parameters": {"scale_multiplier": 0.8, "variance_multiplier": 1.2},
      "prob_home": 0.54,
      "prob_draw": 0.26,
      "prob_away": 0.20,
      "percentiles": {"p5": 0.38, "p25": 0.48, "p50": 0.54, "p75": 0.60, "p95": 0.70},
      "notes": "Lower confidence scenario with higher variance"
    },
    {
      "scenario_type": "base",
      "parameters": {"scale_multiplier": 1.0, "variance_multiplier": 1.0},
      "prob_home": 0.58,
      "prob_draw": 0.24,
      "prob_away": 0.18,
      "percentiles": {"p5": 0.42, "p25": 0.52, "p50": 0.58, "p75": 0.64, "p95": 0.74},
      "notes": "Standard scenario with expected variance"
    },
    {
      "scenario_type": "aggressive",
      "parameters": {"scale_multiplier": 1.2, "variance_multiplier": 0.8},
      "prob_home": 0.62,
      "prob_draw": 0.22,
      "prob_away": 0.16,
      "percentiles": {"p5": 0.48, "p25": 0.56, "p50": 0.62, "p75": 0.68, "p95": 0.78},
      "notes": "Higher confidence scenario with lower variance"
    }
  ],
  
  "uncertainty": {
    "volatility_score": 45.2,
    "data_quality_index": 82.5,
    "confidence_decay": 0.092,
    "factors": {
      "distribution_cv": 0.138,
      "data_age_days": 3.5,
      "feature_coverage": 0.8,
      "sample_size": 1000,
      "event_horizon_days": 7.0
    },
    "notes": "Moderate volatility with good data quality"
  },
  
  "cost_tokens": 2,
  "transaction_id": "tx_abc123",
  "execution_time_ms": 5.2,
  "notes": "Complete distribution analysis"
}
```

**Error Response (Insufficient Tokens)**:
```json
{
  "error": "insufficient_tokens",
  "message": "Insufficient tokens for full_distribution: required=2, available=0",
  "required_tokens": 2,
  "available_tokens": 0,
  "feature": "full_distribution",
  "status": 402
}
```

---

### 2. GET `/api/v2/tokens/balance`

**Purpose**: Check user's token balance.

**Authentication**: Required

**Request Headers**:
```
Authorization: Bearer <your_token>
X-User-ID: <user_id>
```

**Response**:
```json
{
  "user_id": "user_123",
  "balance": 10,
  "last_updated": "2026-02-06T20:45:00Z"
}
```

---

### 3. GET `/api/v2/tokens/ledger`

**Purpose**: Get transaction history for audit purposes.

**Authentication**: Required

**Query Parameters**:
- `limit`: Number of transactions to return (default: 100)

**Response**:
```json
{
  "user_id": "user_123",
  "transactions": [
    {
      "transaction_id": "tx_abc123",
      "timestamp": "2026-02-06T20:40:00Z",
      "feature": "full_distribution",
      "cost": 2,
      "balance_before": 10,
      "balance_after": 8,
      "event_id": "event_123",
      "idempotency_key": "req_xyz",
      "status": "success"
    },
    {
      "transaction_id": "tx_def456",
      "timestamp": "2026-02-06T20:35:00Z",
      "feature": "deep_dive_educational",
      "cost": 5,
      "balance_before": 5,
      "balance_after": 5,
      "event_id": null,
      "status": "denied"
    }
  ]
}
```

---

### 4. POST `/api/v2/tokens/topup`

**Purpose**: Add tokens to user balance (admin/payment endpoint).

**Authentication**: Required (admin)

**Request Body**:
```json
{
  "user_id": "user_123",
  "amount": 20,
  "payment_id": "pay_abc123"
}
```

**Response**:
```json
{
  "user_id": "user_123",
  "balance": 30,
  "amount_added": 20,
  "timestamp": "2026-02-06T20:50:00Z"
}
```

---

### 5. GET `/api/v2/health`

**Purpose**: Health check endpoint.

**Authentication**: None

**Response**:
```json
{
  "status": "healthy",
  "version": "v2.0.0",
  "timestamp": "2026-02-06T20:45:00Z",
  "components": {
    "sim_engine_v2": "ok",
    "uncertainty_metrics": "ok",
    "token_ledger": "ok"
  }
}
```

---

## 🎫 Token Tiers

| Feature | Cost (Tokens) | What You Get |
|---------|---------------|--------------|
| **Headline Pick** | 0 (FREE) | Basic prediction, median probability |
| **Full Distribution** | 2 | Complete percentiles, 3 scenarios, stats |
| **Scenario Extremes** | 3 | Conservative/aggressive bounds analysis |
| **Comparative Analysis** | 3 | Multi-event comparison |
| **Deep Dive Educational** | 5 | Full uncertainty + explainability |

---

## 🔒 Security & Best Practices

### Idempotency
- Use `X-Idempotency-Key` header for all token-consuming requests
- Same key returns same transaction (no double-charge)
- Recommended format: `<user_id>_<timestamp>_<random>`

### Authentication
- All token-gated endpoints require `Authorization` header
- User ID must be provided via `X-User-ID` header
- Free tier (headline pick) doesn't require auth

### Rate Limiting
- Free tier: 100 requests/hour per IP
- Token tiers: 1000 requests/hour per user
- Exceeded limits return 429 (Too Many Requests)

### Error Codes
- `200`: Success
- `400`: Bad request (invalid payload)
- `401`: Unauthorized (missing/invalid auth)
- `402`: Payment required (insufficient tokens)
- `403`: Forbidden (access denied)
- `404`: Not found
- `429`: Too many requests (rate limit)
- `500`: Internal server error

---

## 📊 Data Models

### DistributionObject
See M1_EVIDENCE_REPORT.md for complete schema.

Key fields:
- `percentiles`: P5, P25, P50, P75, P95
- `scenarios`: conservative, base, aggressive
- `uncertainty`: volatility, data_quality, confidence_decay
- `mean`, `stdev`, `skew`, `kurtosis`

### UncertaintyMetrics
See M2_EVIDENCE_REPORT.md for formulas.

- **volatility_score** (0-100): Distribution spread
- **data_quality_index** (0-100): Feature coverage + recency
- **confidence_decay** (0-1/day): Temporal degradation

### TokenTransaction
See M3_EVIDENCE_REPORT.md for audit trail spec.

- All transactions logged (success + denied)
- Idempotency protection built-in
- Refund capability available

---

## 🔄 Backwards Compatibility

### v1 Endpoints (Unchanged)
- `/api/v1/simulate` - Original simulation endpoint
- All existing functionality preserved
- No breaking changes

### Migration Path
1. v1 endpoints remain functional
2. New features only in v2
3. Gradual migration recommended
4. Feature flag `USE_SIM_ENGINE_V2` for rollout control

---

## 📝 Examples

### Free Tier Request (No Auth)
```bash
curl -X POST https://api.trickster-oracle.com/api/v2/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "sport": "soccer",
    "event_id": "example_1",
    "home_rating": 1500,
    "away_rating": 1450,
    "depth": "headline_pick"
  }'
```

### Gated Request (With Tokens)
```bash
curl -X POST https://api.trickster-oracle.com/api/v2/simulate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-User-ID: user_123" \
  -H "X-Idempotency-Key: req_$(date +%s)" \
  -d '{
    "sport": "soccer",
    "event_id": "example_1",
    "home_rating": 1500,
    "away_rating": 1450,
    "depth": "full_distribution",
    "config": {"n_simulations": 1000, "seed": 42}
  }'
```

### Check Balance
```bash
curl -X GET https://api.trickster-oracle.com/api/v2/tokens/balance \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-User-ID: user_123"
```

---

**Version**: 2.0.0  
**Last Updated**: 2026-02-06  
**Status**: Production-Ready (Backend M1-M3 Complete)
