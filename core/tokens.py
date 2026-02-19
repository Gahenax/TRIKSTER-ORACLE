from sqlalchemy.orm import Session
from core.db.models import LedgerEntry
from core.ledger.manager import LedgerManager

class TokenWallet:
    """
    Local token wallet.
    Tokens represent compute/data cost.
    Enforces costs for different operations.
    """
    
    BASE_EVAL_COST = 1
    DEEP_EVAL_COST = 2
    LIVE_SESSION_COST = 2
    COMPARISON_COST = 4
    
    def __init__(self, db_session: Session, ledger: LedgerManager):
        self.db_session = db_session
        self.ledger = ledger

    def get_balance(self) -> int:
        """
        Calculates current balance by summing all token_delta in the ledger.
        Authority: Ledger (via DB mirror for performance).
        """
        from sqlalchemy import func
        # Sum of token_delta across all ledger entries in DB
        delta_sum = self.db_session.query(func.sum(LedgerEntry.data['token_delta'].as_integer())).scalar()
        
        # We start everyone with a 100 token grant (v1 logic)
        BASE_GRANT = 100
        return BASE_GRANT + (delta_sum if delta_sum is not None else 0)

    def spend(self, amount: int, reason: str, event_key: str = "GLOBAL", metadata: dict = None):
        """
        Deducts tokens from balance.
        Checks for sufficient funds before logging.
        """
        current_balance = self.get_balance()
        if current_balance < amount:
            raise ValueError(f"INSUFFICIENT_TOKENS: Required {amount}, available {current_balance}")

        self.ledger.log_event(
            action_type="TOKENS_SPENT",
            event_key=event_key,
            payload={
                "reason": reason,
                "metadata": metadata or {}
            },
            token_delta=-amount # Strict delta format
        )
