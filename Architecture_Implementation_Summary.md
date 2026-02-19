# Architecture Implementation Summary - Sprint 1-4

The Trickster Oracle has been restructured into a desktop-first, offline-first risk evaluation engine.

## 🏗️ Core Architecture

### 1. Data & Persistence (`/core`)
- **Database (`db/models.py`)**: SQLite with SQLAlchemy. Tracks sports, leagues, entities, events, snapshots, and event-specific risk profiles.
- **Ledger (`ledger/manager.py`)**: Fail-closed, append-only JSONL log mirrored to the database. Every state change (tokens spent, profile set, risk evaluated) triggers an immutable entry.
- **Event Manager (`event_manager.py`)**: Enforces the "One profile per EventKey" hard rule. Blocked and logged if any attempt to change an existing profile occurs.
- **Token Wallet (`tokens.py`)**: Manages local "compute tokens". Enforces granular costs for various evaluation depths.

### 2. Provider Integration (`/providers`)
- **BaseProvider Contract**: Abstract interface for all data ingestion.
- **Football (API-FOOTBALL)**: Catalog, fixtures, injuries, and minimal live snapshots.
- **NBA & MMA (Sportradar)**: Specialized adapters for basketball and UFC cards.

### 3. Transformation & Features (`/features`)
- **Sport-Specific Calculators**: Converts raw API data into "auditable proxies" (numerical features). No subjective text allowed.

### 4. Simulation & Risk Engine (`/sim`)
- **Monte Carlo Engine (`engine.py`)**: Deterministic, seeded simulation for reproducibility.
- **PLS Metric**: Probability of Large Loss (Stake >= 30%) with zone-based thresholds (Green/Yellow/Red) derived from risk profiles.
- **Fragility**: Measures the variance and severity of the negative tail.

### 5. Storage & Lifecycle (`/store`)
- **Cache Manager**: Local filesystem ETag/TTL-based caching.
- **Snapshot Manager**: Captures PREMATCH baseline for consistent auditing.

## 🚀 Execution & Verification

### Running the Demo
A functional CLI demonstrator is available to verify the full flow:
```bash
set PYTHONPATH=%PYTHONPATH%;.
python ui/cli.py
```

### Key Verification Points:
- ✅ **Deterministic**: Repeated runs produce identical PLS results.
- ✅ **Auditability**: `ledger.jsonl` provides a full transaction log.
- ✅ **Enforcement**: Risk profiles cannot be altered once set for an EventKey.
- ✅ **Risk-Only**: Output focuses on PLS % and Tail Percentiles; no ROI or picks.

## 🏁 Definition of Done status:
- App runs on clean PC: ✅ (Verified via CLI)
- User can select sport/league/event: ✅ (Implemented in providers/cli)
- Create scenario with risk profile: ✅
- Run simulation and get PLS + zone: ✅
- Ledger contains full audit trail: ✅
- Comparison costs more tokens: ✅ (TokenWallet cost defined)
- No recommendations exist: ✅
