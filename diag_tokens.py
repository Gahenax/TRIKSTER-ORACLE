import os
import pytest
from main import TricksterOracleApp

def test_token_balance_calc():
    db_path = "diag_tokens.db"
    ledger_path = "diag_tokens.jsonl"
    if os.path.exists(db_path): os.remove(db_path)
    if os.path.exists(ledger_path): os.remove(ledger_path)
    
    app = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    
    # 1. Check initial balance
    bal = app.tokens.get_balance()
    print(f"Initial balance: {bal}")
    assert bal == 100
    
    # 2. Spend tokens
    app.tokens.spend(10, "First spend")
    bal = app.tokens.get_balance()
    print(f"Balance after 10 spend: {bal}")
    assert bal == 90
    
    # 3. Exhaust tokens
    app.tokens.spend(90, "Exhausting")
    assert app.tokens.get_balance() == 0
    
    # 4. Try to overspend
    try:
        app.tokens.spend(1, "Overspend")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Caught expected error: {e}")
        assert "INSUFFICIENT_TOKENS" in str(e)

    # 5. Verify rehydration maintains balance
    app.shutdown()
    os.remove(db_path)
    
    app2 = TricksterOracleApp(db_path=db_path, ledger_path=ledger_path)
    bal2 = app2.tokens.get_balance()
    print(f"Rehydrated balance: {bal2}")
    assert bal2 == 0
    app2.shutdown()

if __name__ == "__main__":
    test_token_balance_calc()
