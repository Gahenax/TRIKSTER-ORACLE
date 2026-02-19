from main import TricksterOracleApp
from sim.scenario import Scenario
from core.db.models import RiskProfileEnum
from datetime import datetime, timezone

def run_demo_cli():
    app = TricksterOracleApp()
    
    print("\n--- TRICKSTER ORACLE v1 ---")
    print("Risk-First Evaluation Engine\n")
    
    # 1. Selection Simulation
    sport = "FOOTBALL"
    league = "Premier League"
    home = "Manchester City"
    away = "Liverpool"
    date = datetime(2026, 2, 15)
    
    from core.utils import generate_event_key
    event_key = generate_event_key(sport, league, home, away, date)
    
    print(f"Selected Event: {home} vs {away} ({league})")
    print(f"EventKey: {event_key[:12]}...")
    
    # 2. Set Risk Profile
    profile = RiskProfileEnum.NEUTRAL
    try:
        app.event_manager.set_risk_profile(event_key, profile)
        print(f"Risk Profile Set: {profile}")
    except ValueError as e:
        print(f"Notice: {e}")

    # 3. Create Scenario (Updated for Sprint 6/7/8)
    stake = 100.0
    features = {
        "rating_diff": 50.0,
        "home_advantage": 100.0,
        "home_availability_ratio": 0.95,
        "away_availability_ratio": 0.88
    }
    
    # Snapshot simulation
    snapshot_id = "snap_demo_1"
    snapshot_data = {"home": home, "away": away, "date": date.isoformat()}
    
    print(f"\nEvaluating Scenario: Stake={stake}, Profile={profile}")
    
    # 4. Token Cost
    cost = app.tokens.BASE_EVAL_COST
    app.tokens.spend(cost, "Evaluation", event_key=event_key)
    print(f"Tokens Spent: {cost}")
    
    # 5. Run Sim
    scenario = Scenario(
        event_key=event_key, 
        risk_profile=profile, 
        stake=stake, 
        features=features,
        snapshot_id=snapshot_id,
        snapshot_data=snapshot_data
    )
    result = scenario.evaluate() # Uses adaptive sims from Sprint 8
    
    # 6. Display Result (Sober, No Recommendations)
    print("\n--- RESULTS ---")
    print(f"PLS (Prob. Large Loss): {result['pls']*100:.2f}%")
    print(f"RISK ZONE: [{result['zone']}]")
    print(f"Fragility Indicator: {result['fragility']:.4f}")
    print(f"Simulations Performed: {result['n_sims']}")
    print(f"Determinism Signature: {result['determinism_signature'][:12]}...")
    
    print("\nTail Percentiles (Loss Potential):")
    for p, val in result['tail_percentiles'].items():
        print(f"  {p}: {val*100:.1f}%")
    
    print("\n--- AUDIT LEDGER ---")
    print("Event logged to ledger.jsonl")
    
    # 7. Export Report Pack (Sprint W1)
    from core.exporter import ReportExporter
    exporter = ReportExporter()
    
    # Map result to export schema
    export_data = {
        "app_version": "1.0.0-desktop",
        "policy_version": "1.0.0-risk-only",
        "event_key": event_key,
        "snapshot_id": snapshot_id,
        "seed": 42,
        "config": {"n_sims": result['n_sims']},
        "features_summary": {k: float(v) for k, v in features.items() if isinstance(v, (int, float))},
        "results": {
            "pls_percent": float(result['pls']),
            "zone": result['zone'],
            "tail_percentiles": {k: float(v) for k, v in result['tail_percentiles'].items()},
            "fragility": float(result['fragility'])
        },
        "audit": {
            "determinism_signature": result['determinism_signature'],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "inputs_hashes": {} # Placeholder for snapshot/features hashes
        }
    }
    
    try:
        pack_path = exporter.export_pack(export_data)
        print(f"\n[EXPORT] Report Pack generated successfully: {pack_path}")
    except Exception as e:
        print(f"\n[EXPORT ERROR] Failed to generate report pack: {e}")

    app.shutdown()

if __name__ == "__main__":
    run_demo_cli()
