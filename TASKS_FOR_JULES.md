# TASKS FOR JULES — Trickster Oracle FASE 1

**Repository**: https://github.com/Gahenax/TRIKSTER-ORACLE  
**Branch**: `feature/phase1-monte-carlo-engine`  
**Assigned to**: Google Jules  
**Context**: Educational probabilistic analytics platform. See README.md and GLOSSARY.md for anti-gambling stance.

---

## 🎯 TASK 1: Implement Monte Carlo Engine (T1.1)

**Goal**: Create deterministic Monte Carlo simulation engine with reproducibility.

### Files to Create/Modify:

#### 1. `backend/app/core/model.py`
```python
"""
ELO-based probability model for match outcomes
REQUIREMENTS:
- Implement calculate_probabilities(home_rating, away_rating, home_advantage) -> dict
- Return: {prob_home, prob_draw, prob_away} (must sum to 1.0)
- Use standard ELO formula: expected = 1 / (1 + 10^((rating_diff)/400))
- For 3-outcome (draw): use adjusted formula with draw probability ~20-30% for equal teams
- Must be deterministic (no randomness in probability calculation)
"""
```

#### 2. `backend/app/core/engine.py`
```python
"""
Monte Carlo simulation engine
REQUIREMENTS:
- Function: simulate_event(event: EventInput, config: SimConfig) -> dict
- Use model.py to get base probabilities
- Run n_simulations Monte Carlo iterations
- CRITICAL: Use numpy.random.seed(config.seed) if seed provided for reproducibility
- Return:
  * prob_home, prob_draw, prob_away (aggregated from simulations)
  * distribution: histogram data (bins + frequencies)
  * confidence_intervals: calculate CI at 95% and 99% levels using numpy.percentile
  * execution_time_ms: measure simulation time
- Distribution should be stored as {"bins": [0.0, 0.1, ..., 1.0], "frequencies": [n1, n2, ...]}
"""
```

#### 3. `backend/app/core/risk.py`
```python
"""
Risk assessment module
REQUIREMENTS:
- Function: calculate_risk(distribution: dict, probabilities: dict) -> RiskInfo
- Calculate risk score (0-100) based on:
  * Variance/std of distribution
  * Confidence interval width
  * Entropy of probability distribution
- Assign risk band:
  * LOW: score < 30 (tight distribution, high confidence)
  * MEDIUM: score 30-60 (moderate uncertainty)
  * HIGH: score > 60 (wide distribution, high uncertainty)
- Generate human-readable rationale (1-2 sentences)
- Use terminology from GLOSSARY.md (no gambling language!)
"""
```

#### 4. `backend/app/data/sample_events.json`
```json
[
  {
    "event_id": "demo_001",
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "home_rating": 2100,
    "away_rating": 2050,
    "home_advantage": 100,
    "sport": "football"
  },
  {
    "event_id": "demo_002",
    "home_team": "Barcelona",
    "away_team": "Real Madrid",
    "home_rating": 2080,
    "away_rating": 2120,
    "home_advantage": 100,
    "sport": "football"
  },
  {
    "event_id": "demo_003",
    "home_team": "Bayern Munich",
    "away_team": "Borussia Dortmund",
    "home_rating": 2150,
    "away_rating": 1980,
    "home_advantage": 100,
    "sport": "football"
  }
]
```

---

## 🧪 TASK 2: Create Unit Tests (T1.1 DoD)

**Goal**: Ensure deterministic behavior and correctness.

### Files to Create:

#### 1. `backend/app/tests/test_engine.py`
```python
"""
REQUIRED TESTS:
1. test_engine_determinism():
   - Run same event with same seed twice
   - Assert all outputs are identical (probabilities, distribution, CI)
   
2. test_engine_different_seeds():
   - Run same event with different seeds
   - Assert outputs differ
   
3. test_probabilities_sum_to_one():
   - Test multiple events
   - Assert prob_home + prob_draw + prob_away ≈ 1.0 (within 0.001)
   
4. test_confidence_intervals():
   - Assert CI_99 is wider than CI_95
   - Assert probabilities fall within CI ranges
   
5. test_n_sims_validation():
   - Test with n_sims=100 (min), n_sims=1000 (default), n_sims=10000 (max)
   - Assert validation works correctly
"""
```

#### 2. `backend/app/tests/test_risk.py`
```python
"""
REQUIRED TESTS:
1. test_risk_bands():
   - Create 3 test distributions: narrow (LOW), medium (MEDIUM), wide (HIGH)
   - Assert correct band assignment
   
2. test_risk_score_range():
   - Assert score is always 0-100
   
3. test_no_forbidden_terms():
   - Assert rationale doesn't contain: bet, pick, odd, guaranteed, sure
   - Use forbidden terms list from GLOSSARY.md
"""
```

---

## 📋 Definition of Done (DoD)

Before submitting PR, verify:

- [ ] `pytest backend/app/tests/` passes with 100% success
- [ ] `test_engine_determinism` passes (same input+seed → same output)
- [ ] All probabilities sum to 1.0 (±0.001 tolerance)
- [ ] Risk rationale uses only permitted terminology (check GLOSSARY.md)
- [ ] Code is formatted with `black` (line-length=100)
- [ ] No hardcoded values; use constants or config
- [ ] Sample events load correctly from JSON
- [ ] Execution time is logged and reasonable (<2s for 1000 sims)

---

## 🚨 Critical Requirements

1. **Determinism**: Same input + seed MUST produce identical outputs
2. **No Gambling Language**: Check GLOSSARY.md for forbidden terms
3. **Proper Error Handling**: Validate inputs, return structured errors
4. **Documentation**: Docstrings for all public functions
5. **Type Hints**: Use Python type annotations throughout

---

## 📝 Commit Message Format

Use format: `T1.1 — [component] description`

Examples:
- `T1.1 — Implement ELO probability model`
- `T1.1 — Add Monte Carlo engine with deterministic seeding`
- `T1.1 — Implement risk scoring with LOW/MEDIUM/HIGH bands`
- `T1.1 — Add unit tests for engine determinism`

---

## 🔗 Dependencies

Install with:
```bash
cd backend
pip install -e ".[dev]"
```

---

## 📤 Deliverables

1. **Pull Request** to `master` branch with title: `FASE 1 — Monte Carlo Engine & Risk Assessment`
2. **All tests passing** (include pytest output in PR description)
3. **Example output** (JSON) from running simulation with sample event
4. **Performance metrics** (execution time for 100, 1000, 10000 simulations)

---

## 💡 Notes for Jules

- The project prioritizes **education and transparency** over prediction accuracy
- Risk assessment should help users understand uncertainty, not hide it
- If you encounter ambiguity, favor the more conservative/cautious approach
- Check existing `schemas.py` for data structures (EventInput, SimulationConfig, etc.)
- Model version should be "0.1.0" (from app.__version__)

---

**Estimated Time**: 2-4 hours  
**Priority**: HIGH (blocks FASE 2 & 3)  
**Questions**: Comment on this issue or check ROADMAP.py for full context
