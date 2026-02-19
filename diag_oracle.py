from oracle.pipeline import evaluate_oracle_request
import json

def test_oracle_pipeline():
    request = {
        "sport": "FOOTBALL",
        "primary": "Real Madrid",
        "opponent": "Barcelona",
        "rating_diff": 150.0,
        "risk_profile": "CONSERVATIVE",
        "stake": 100.0
    }
    
    print("Testing Oracle Pipeline (Risk-First)...")
    try:
        result = evaluate_oracle_request(request)
        print(json.dumps(result, indent=2))
        
        # Verify no forbidden terms in text
        title = result["text"]["title"]
        assert "oportunidad" not in title.lower()
        assert "ganador" not in title.lower()
        
        print("\nPipeline Verification: SUCCESS")
    except Exception as e:
        print(f"\nPipeline Verification: FAILED - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_oracle_pipeline()
