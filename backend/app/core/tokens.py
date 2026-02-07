"""
Token Gating Module - M3: TOKEN_GATING_ANALYTICS_ACCESS

Implements token-based access control for analytics features.

KEY PRINCIPLE: 
"Tokens buy depth (analysis, scenarios, export), NOT 'winning picks'"

Access Tiers:
- Headline pick: FREE (0 tokens)
- Full distribution: 2 tokens
- Scenario extremes: 3 tokens
- Comparative analysis: 3 tokens
- Deep dive educational: 5 tokens

Features:
- Server-side enforcement
- Audit logging of all transactions
- Idempotency protection (no double-charge on retries)
- User balance tracking
"""

from typing import Dict, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class FeatureTier(str, Enum):
    """Analytics feature access tiers"""
    HEADLINE_PICK = "headline_pick"
    FULL_DISTRIBUTION = "full_distribution"
    SCENARIO_EXTREMES = "scenario_extremes"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    DEEP_DIVE_EDUCATIONAL = "deep_dive_educational"


# Token cost configuration
FEATURE_COSTS: Dict[FeatureTier, int] = {
    FeatureTier.HEADLINE_PICK: 0,
    FeatureTier.FULL_DISTRIBUTION: 2,
    FeatureTier.SCENARIO_EXTREMES: 3,
    FeatureTier.COMPARATIVE_ANALYSIS: 3,
    FeatureTier.DEEP_DIVE_EDUCATIONAL: 5,
}


class TokenTransaction(BaseModel):
    """Record of a token transaction"""
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    feature: FeatureTier
    cost: int
    balance_before: int
    balance_after: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    status: str = Field(default="success")  # success | denied | refunded


class TokenBalance(BaseModel):
    """User token balance"""
    user_id: str
    balance: int = Field(ge=0)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccessDeniedError(Exception):
    """Raised when user has insufficient tokens"""
    def __init__(self, feature: FeatureTier, required: int, available: int):
        self.feature = feature
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient tokens for {feature.value}: required={required}, available={available}"
        )


class TokenLedger:
    """
    In-memory token ledger with audit trail.
    
    Production: Replace with Redis or database backend.
    """
    
    def __init__(self):
        self._balances: Dict[str, int] = {}  # user_id -> balance
        self._transactions: List[TokenTransaction] = []
        self._idempotency_cache: Dict[str, str] = {}  # idempotency_key -> transaction_id
    
    def get_balance(self, user_id: str) -> int:
        """Get current token balance for user"""
        return self._balances.get(user_id, 0)
    
    def set_balance(self, user_id: str, balance: int) -> None:
        """Set token balance for user (admin/top-up operation)"""
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        self._balances[user_id] = balance
    
    def add_tokens(self, user_id: str, amount: int) -> int:
        """Add tokens to user balance (top-up)"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        current = self.get_balance(user_id)
        new_balance = current + amount
        self._balances[user_id] = new_balance
        return new_balance
    
    def check_access(
        self,
        user_id: str,
        feature: FeatureTier
    ) -> bool:
        """
        Check if user has sufficient tokens for feature.
        Does NOT deduct tokens (read-only check).
        """
        required = FEATURE_COSTS[feature]
        available = self.get_balance(user_id)
        return available >= required
    
    def consume_tokens(
        self,
        user_id: str,
        feature: FeatureTier,
        event_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> TokenTransaction:
        """
        Consume tokens for feature access.
        
        Args:
            user_id: User identifier
            feature: Feature being accessed
            event_id: Optional event ID for audit trail
            idempotency_key: Optional key to prevent double-charging
        
        Returns:
            TokenTransaction record
        
        Raises:
            AccessDeniedError: If insufficient tokens
        """
        # Idempotency check: return cached transaction if key exists
        if idempotency_key and idempotency_key in self._idempotency_cache:
            cached_tx_id = self._idempotency_cache[idempotency_key]
            # Find transaction
            for tx in self._transactions:
                if tx.transaction_id == cached_tx_id:
                    return tx
        
        required = FEATURE_COSTS[feature]
        available = self.get_balance(user_id)
        
        # Check sufficiency
        if available < required:
            # Log denied transaction
            denied_tx = TokenTransaction(
                user_id=user_id,
                feature=feature,
                cost=required,
                balance_before=available,
                balance_after=available,
                event_id=event_id,
                idempotency_key=idempotency_key,
                status="denied"
            )
            self._transactions.append(denied_tx)
            raise AccessDeniedError(feature, required, available)
        
        # Deduct tokens
        new_balance = available - required
        self._balances[user_id] = new_balance
        
        # Record transaction
        transaction = TokenTransaction(
            user_id=user_id,
            feature=feature,
            cost=required,
            balance_before=available,
            balance_after=new_balance,
            event_id=event_id,
            idempotency_key=idempotency_key,
            status="success"
        )
        
        self._transactions.append(transaction)
        
        # Cache idempotency key
        if idempotency_key:
            self._idempotency_cache[idempotency_key] = transaction.transaction_id
        
        return transaction
    
    def refund_transaction(self, transaction_id: str) -> TokenTransaction:
        """
        Refund a transaction (return tokens to user).
        
        Args:
            transaction_id: ID of transaction to refund
        
        Returns:
            New refund transaction
        
        Raises:
            ValueError: If transaction not found or already refunded
        """
        # Find original transaction
        original_tx = None
        for tx in self._transactions:
            if tx.transaction_id == transaction_id:
                original_tx = tx
                break
        
        if not original_tx:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if original_tx.status == "refunded":
            raise ValueError(f"Transaction {transaction_id} already refunded")
        
        # Restore tokens
        current_balance = self.get_balance(original_tx.user_id)
        new_balance = current_balance + original_tx.cost
        self._balances[original_tx.user_id] = new_balance
        
        # Mark original as refunded
        original_tx.status = "refunded"
        
        # Create refund transaction
        refund_tx = TokenTransaction(
            user_id=original_tx.user_id,
            feature=original_tx.feature,
            cost=-original_tx.cost,  # Negative cost = refund
            balance_before=current_balance,
            balance_after=new_balance,
            event_id=original_tx.event_id,
            status="refunded"
        )
        
        self._transactions.append(refund_tx)
        return refund_tx
    
    def get_transaction_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[TokenTransaction]:
        """Get transaction history for user"""
        user_txs = [
            tx for tx in self._transactions 
            if tx.user_id == user_id
        ]
        # Most recent first
        user_txs.sort(key=lambda x: x.timestamp, reverse=True)
        return user_txs[:limit]
    
    def get_all_transactions(self, limit: int = 1000) -> List[TokenTransaction]:
        """Get all transactions (admin/audit purpose)"""
        txs = list(self._transactions)
        txs.sort(key=lambda x: x.timestamp, reverse=True)
        return txs[:limit]


# Global ledger instance
# Production: Uses Redis with in-memory fallback
import os
from app.core.redis_ledger import RedisTokenLedger

_global_ledger = RedisTokenLedger(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD")
)


def get_ledger() -> TokenLedger:
    """Get the global token ledger instance"""
    return _global_ledger


def require_tokens(
    user_id: str,
    feature: FeatureTier,
    event_id: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> TokenTransaction:
    """
    Convenience function to require tokens for a feature.
    
    Usage in API endpoints:
        transaction = require_tokens(
            user_id="user123",
            feature=FeatureTier.FULL_DISTRIBUTION,
            event_id=event.event_id,
            idempotency_key=request.headers.get("Idempotency-Key")
        )
    
    Raises:
        AccessDeniedError: If insufficient tokens
    """
    ledger = get_ledger()
    return ledger.consume_tokens(user_id, feature, event_id, idempotency_key)


def check_feature_access(user_id: str, feature: FeatureTier) -> bool:
    """
    Check if user can access feature (without consuming tokens).
    
    Useful for UI to show/hide features based on balance.
    """
    ledger = get_ledger()
    return ledger.check_access(user_id, feature)
