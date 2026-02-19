# Architecture: Persistence Authority

## Authority Hierarchy
1. **Source of Truth (L0)**: `ledger.jsonl`
   - Every state-changing operation MUST append to this file before completing.
   - It is an append-only, ordered log of events.
   - If writing to L0 fails, the system MUST abort the operation (Fail-Closed).

2. **Materialized Index (L1)**: SQLite Database (`oracle.db`)
   - The database is a projections/cache of the ledger.
   - It provides high-performance querying and relational lookups.
   - The database is *subordinate* to the ledger.

## Recovery & Rehydration
In the event of database corruption or deletion:
- The system must provide a `rehydrate_db_from_ledger` routine.
- This routine reads `ledger.jsonl` from the beginning and replays all events into a fresh SQLite database.
- Integrity Check: If the DB state diverges from the ledger replay, the DB version must be considered invalid and overwritten by the ledger's authority.

## Failure Modes
- **Ledger Write Failure**: Immediate stop. System enters read-only or error state.
- **Ledger Corruption (Partial Lines)**: Detected on startup via integrity scan. System requires manual audit or truncation of the corrupted line.
- **DB/Ledger Divergence**: Ledger wins. Trigger rehydration.
