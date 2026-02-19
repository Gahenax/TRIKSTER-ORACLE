# JULES WORK ORDER: Kernel Integration Phase 3-5

**Project**: Trickster Oracle - Kernel Integration  
**Assigned to**: Jules (AI Pair Programmer)  
**Coordinator**: Antigravity  
**Priority**: Medium (Parallel work while Antigravity handles endpoint integration)  
**Estimated Effort**: 3-4 work cycles

---

## Context

Trickster Oracle backend now has kernel infrastructure operational (Phase 1 ✅, Phase 2 ✅). You will implement remaining components for Phases 3-5 while Antigravity integrates the kernel into the main `/api/v2/simulate` endpoint.

**Critical Constraints**:
- Do NOT modify existing test files in `app/tests/`
- All new code must pass existing test suite (84 tests)
- Follow existing code style (see `backend/app/core/`)
- Use type hints and docstrings

## Task 0: Spectral Chaos Calibration (NEW IMPROVEMENT)

**Goal**: Calibration of the Monte Carlo engine against Random Matrix Theory (RMT) signatures. The engine must now audit its own "entropy quality".

- **New Dependency**: `backend/app/core/spectral.py`
- **Requirement**: All simulation outputs must now include a `spectral_report` in their internal state.
- **Verification**: The code in `backend/app/core/engine.py` has been updated to include an `r-mean` audit. Ensure that any future changes to the simulation logic (Task 2/3) do not degrade the `r-mean` below chaotic thresholds (GUE ~ 0.60).

---

## Task 1: History Provider for TrueSkill Through Time

**File**: `backend/app/ratings/history_provider.py` (NEW)

**Objective**: Create a history provider that returns fighter bout history with timestamps for TTT rating calculations.

### Requirements

1. **Create `HistoryProvider` class**:
   ```python
   class HistoryProvider:
       def __init__(self, data_source: Optional[str] = None):
           """
           Initialize history provider.
           Args:
               data_source: Optional path to CSV/JSON file with bout history
           """
           # For now, use in-memory mock data
           # Future: load from file or database
   
       def get_history(self, fighter_a: str, fighter_b: str) -> List[Dict[str, Any]]:
           """
           Get bout history for two fighters.
           
           Returns list of bouts in chronological order:
           [
               {"a": "FighterX", "b": "FighterY", "winner": "FighterX", "date": "2025-01-15"},
               ...
           ]
           """
   ```

2. **Mock Data Implementation**:
   - Create at least 20 sample bouts between 5-10 fictional fighters
   - Include dates spanning 6-12 months
   - Ensure some fighters have transitive relationships (A beat B, B beat C)
   - Include at least one non-transitive cycle for testing

3. **Integration**:
   - Update `backend/app/ratings/ttt_adapter.py`:
     - Import `HistoryProvider`
     - Modify `build_rating_provider` to accept `history_provider: HistoryProvider`
   - The provider should filter history to only bouts involving fighter_a OR fighter_b

### Testing

Create `backend/tests/test_history_provider.py`:
- Test `get_history` returns correct bout structure
- Test filtering works (only relevant bouts returned)
- Test chronological ordering
- Test empty history for unknown fighters

**Acceptance Criteria**:
- ✅ `HistoryProvider` class implemented with mock data
- ✅ At least 4 tests passing in `test_history_provider.py`
- ✅ Integration updated in `ttt_adapter.py`
- ✅ Existing tests still pass

---

## Task 2: Matchup Graph Builder

**File**: `backend/app/sim_kernel/graph_builder.py` (NEW)

**Objective**: Create a matchup graph builder that constructs a local neighborhood graph around two fighters and detects non-transitive patterns.

### Requirements

1. **Create `MatchupGraphBuilder` class**:
   ```python
   class MatchupGraphBuilder:
       def __init__(self, history_provider):
           """Initialize with history provider."""
           self.history_provider = history_provider
   
       def build_graph(
           self,
           request: Dict[str, Any],
           features: Optional[Dict] = None,
           rating: Optional[Dict] = None,
           max_nodes: int = 40,
           seed: int = 1337
       ) -> Dict[str, Any]:
           """
           Build matchup graph around fighter_a and fighter_b.
           
           Returns:
           {
               "nodes": ["FighterA", "FighterB", "FighterC", ...],
               "edges": [
                   {"u": "FighterA", "v": "FighterB", "p": 0.65},
                   ...
               ]
           }
           
           Where p = estimated probability that u beats v based on history.
           """
   ```

2. **Graph Construction Logic**:
   - Start with fighter_a and fighter_b as seed nodes
   - Expand to include fighters who have fought either seed (1-hop neighbors)
   - Limit total nodes to `max_nodes`
   - Calculate edge probabilities based on:
     - Direct matchup history (if exists)
     - Rating differential (if ratings provided)
     - Fallback to 0.5 if no data

3. **Probability Estimation**:
   ```python
   def _estimate_probability(self, fighter_u: str, fighter_v: str, history: List[Dict]) -> float:
       """
       Estimate P(u beats v) from history.
       
       If direct matchups exist:
           p = wins_u / (wins_u + wins_v)
       
       If no direct matchups but ratings exist:
           Use logistic function on rating diff
       
       Else:
           return 0.5
       """
   ```

### Testing

Create `backend/tests/test_graph_builder.py`:
- Test graph construction with 2 fighters
- Test expansion to neighbors
- Test max_nodes constraint honored
- Test probability estimation from history
- Test cycle detection integration

**Acceptance Criteria**:
- ✅ `MatchupGraphBuilder` class implemented
- ✅ At least 5 tests passing in `test_graph_builder.py`
- ✅ Integration with `MatchupGraphAction` (update to use real builder)
- ✅ Existing tests still pass

---

## Task 3: Additional Scenario Fixtures

**Directory**: `backend/tests/scenarios/` (ADD FILES)

**Objective**: Create more scenario JSON fixtures for regression testing.

### Scenarios to Create

1. **`priority_scheduler_001.json`**:
   ```json
   {
     "id": "priority_scheduler_001",
     "request": {"fighter_a": "A", "fighter_b": "B"},
     "config": {"scheduler": "PRIORITY", "seed": 42, "depth": "standard"},
     "assert": {
       "journal_steps_count": 4,
       "first_step_name": "ingest"
     }
   }
   ```

2. **`budget_degradation_001.json`**:
   ```json
   {
     "id": "budget_degradation_001",
     "request": {"fighter_a": "X", "fighter_b": "Y"},
     "config": {
       "scheduler": "FIFO",
       "seed": 7,
       "depth": "standard",
       "budget": {
         "max_ms_total": 200,
         "max_mc_runs": 1000,
         "max_graph_nodes": 40,
         "max_explain_chars": 2000
       }
     },
     "assert": {
       "degraded": true,
       "degrade_reason_contains": "low_time_budget"
     }
   }
   ```

3. **`rating_integration_001.json`**:
   - Test rating baseline action with TTT provider
   - Verify rating artifacts present in state

4. **`full_pipeline_001.json`**:
   - Test complete pipeline: ingest → rating → graph → mc → explain → emit
   - Verify all steps execute successfully

### Update Test Runner

Update `backend/tests/test_scenarios_runner.py`:
- Extend assertion logic to support new assertion types:
  - `journal_steps_count`
  - `first_step_name`
  - `degraded`
  - `degrade_reason_contains`
- Keep backward compatible with existing assertion format

**Acceptance Criteria**:
- ✅ At least 4 new scenario JSON files created
- ✅ `test_scenarios_runner.py` updated to handle new assertions
- ✅ All scenario tests pass

---

## Task 4: API Documentation Update

**File**: `backend/API_DOCUMENTATION.md` (MODIFY)

**Objective**: Document new observability fields in API responses.

### What to Add

Add section "**Kernel Observability Metadata**" after existing endpoint documentation:

```markdown
### Kernel Observability Metadata

All `/api/v2/simulate` responses now include optional observability fields in the `meta` object:

#### Response Meta Fields

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique UUID for this simulation run (hex format) |
| `degraded` | boolean | True if execution was degraded due to budget constraints |
| `degrade_reason` | string? | Reason for degradation (e.g., "low_time_budget_reduce_mc") |
| `warnings` | string[]? | List of non-critical warnings (e.g., "feature_extractor_not_wired") |

#### Example Response with Observability

```json
{
  "distribution": { ... },
  "uncertainty": { ... },
  "cost_tokens": 2,
  "transaction_id": "tx_abc123",
  "user_status": { ... },
  "notes": "Full distribution analysis",
  "meta": {
    "run_id": "a1b2c3d4e5f6",
    "degraded": false,
    "warnings": []
  }
}
```

#### Budget Degradation Example

When time budget is insufficient:

```json
{
  "meta": {
    "run_id": "x9y8z7",
    "degraded": true,
    "degrade_reason": "low_time_budget_reduce_mc",
    "warnings": ["mc_runs_reduced_from_1000_to_80"]
  }
}
```
```

**Acceptance Criteria**:
- ✅ Documentation updated with observability section
- ✅ Examples provided for normal and degraded responses
- ✅ Table formatting correct

---

## Testing Instructions

After completing each task:

1. **Run specific tests**:
   ```bash
   cd backend
   pytest tests/test_history_provider.py -v
   pytest tests/test_graph_builder.py -v
   pytest tests/test_scenarios_runner.py -v
   ```

2. **Run full regression**:
   ```bash
   pytest app/tests/ -q
   ```
   All 84 existing tests must pass.

3. **Run all kernel tests**:
   ```bash
   pytest tests/ -v
   ```

---

## Deliverables Checklist

- [ ] `backend/app/ratings/history_provider.py` created
- [ ] `backend/tests/test_history_provider.py` created (≥4 tests passing)
- [ ] `backend/app/ratings/ttt_adapter.py` updated to use HistoryProvider
- [ ] `backend/app/sim_kernel/graph_builder.py` created
- [ ] `backend/tests/test_graph_builder.py` created (≥5 tests passing)
- [ ] `backend/app/sim_kernel/actions/matchup_graph.py` updated to use real builder
- [ ] 4+ scenario JSON files created in `backend/tests/scenarios/`
- [ ] `backend/tests/test_scenarios_runner.py` updated for new assertions
- [ ] `backend/API_DOCUMENTATION.md` updated with observability section
- [ ] All existing tests still passing (84/84)
- [ ] All new tests passing

---

## Communication Protocol

**Report after each task**:
1. Files created/modified
2. Test results (pass/fail counts)
3. Any blockers or questions
4. Next task you're starting

**On completion**:
- Create a summary report of all changes
- Confirm all tests passing
- Flag any TODOs or technical debt introduced

---

## Notes for Jules

- Take your time to understand the existing codebase patterns
- Look at `backend/app/core/engine.py` and `backend/app/core/explain.py` for style reference
- If you encounter import errors, check that `__init__.py` files exist
- Mock data is fine for history provider - we'll replace with real DB later
- Ask Antigravity if you need clarification on kernel architecture

**Priority Order**: Task 1 → Task 2 → Task 3 → Task 4

Good luck! 🚀
