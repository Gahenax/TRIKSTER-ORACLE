from __future__ import annotations
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
import redis
from app.core.tokens import TokenLedger, TokenTransaction, FeatureTier

logger = logging.getLogger(__name__)

class RedisTokenLedger(TokenLedger):
    """
    Redis-backed token ledger for production persistence.
    Uses Redis hashes for balances and lists for transaction history.
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        super().__init__()
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password, 
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.client.ping()
            self.use_redis = True
            logger.info(f"Connected to Redis for TokenLedger at {host}:{port}")
        except (redis.ConnectionError, redis.TimeoutError):
            self.use_redis = False
            logger.warning("Could not connect to Redis. Falling back to in-memory TokenLedger.")

    def _get_balance_key(self, user_id: str) -> str:
        return f"tokens:balance:{user_id}"

    def _get_tx_key(self, user_id: str) -> str:
        return f"tokens:transactions:{user_id}"

    def _get_idempotency_key(self, key: str) -> str:
        return f"tokens:idempotency:{key}"

    def _get_status_key(self, user_id: str) -> str:
        return f"tokens:status:{user_id}"

    def get_balance(self, user_id: str) -> int:
        if not self.use_redis:
            return super().get_balance(user_id)
        
        balance = self.client.get(self._get_balance_key(user_id))
        return int(balance) if balance else 0

    def set_balance(self, user_id: str, balance: int) -> None:
        if not self.use_redis:
            return super().set_balance(user_id, balance)
        
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        self.client.set(self._get_balance_key(user_id), balance)

    def add_tokens(self, user_id: str, amount: int) -> int:
        if not self.use_redis:
            return super().add_tokens(user_id, amount)
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        new_balance = self.client.incrby(self._get_balance_key(user_id), amount)
        return new_balance

    def consume_tokens(
        self,
        user_id: str,
        feature: FeatureTier,
        event_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> TokenTransaction:
        if not self.use_redis:
            return super().consume_tokens(user_id, feature, event_id, idempotency_key)

        # Check idempotency
        if idempotency_key:
            cached_tx = self.client.get(self._get_idempotency_key(idempotency_key))
            if cached_tx:
                return TokenTransaction.model_validate_json(cached_tx)

        required = 0 # Cost logic
        from app.core.tokens import FEATURE_COSTS
        required = FEATURE_COSTS[feature]
        
        # Atomic check and deduct using Lua script or Watch
        # Simplified for now (ideally use Lua for atomicity)
        current = self.get_balance(user_id)
        if current < required:
            # Note: We don't store denied tx in Redis primary list to save space
            from app.core.tokens import AccessDeniedError
            raise AccessDeniedError(feature, required, current)

        new_balance = self.client.decrby(self._get_balance_key(user_id), required)
        
        transaction = TokenTransaction(
            user_id=user_id,
            feature=feature,
            cost=required,
            balance_before=current,
            balance_after=new_balance,
            event_id=event_id,
            idempotency_key=idempotency_key,
            status="success"
        )
        
        # Save transaction
        tx_json = transaction.model_dump_json()
        self.client.lpush(self._get_tx_key(user_id), tx_json)
        self.client.ltrim(self._get_tx_key(user_id), 0, 99) # Keep last 100
        
        if idempotency_key:
            self.client.setex(self._get_idempotency_key(idempotency_key), 86400, tx_json) # 24h

        return transaction

    def get_transaction_history(self, user_id: str, limit: int = 100) -> List[TokenTransaction]:
        if not self.use_redis:
            return super().get_transaction_history(user_id, limit)
        
        txs_json = self.client.lrange(self._get_tx_key(user_id), 0, limit - 1)
        return [TokenTransaction.model_validate_json(tx) for tx in txs_json]

    def get_user_status(self, user_id: str) -> UserStatus:
        from app.core.tokens import UserStatus
        if not self.use_redis:
            return super().get_user_status(user_id)

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        data = self.client.hgetall(self._get_status_key(user_id))
        
        if not data:
            # New user status
            status = UserStatus(
                user_id=user_id,
                token_balance=self.get_balance(user_id),
                last_reset=today_start
            )
            self._save_status(status)
            return status

        # Check for day reset
        last_reset = datetime.fromisoformat(data['last_reset'])
        if last_reset < today_start:
            # Daily reset
            self.client.hset(self._get_status_key(user_id), mapping={
                "daily_used": 0,
                "last_reset": today_start.isoformat()
            })
            data['daily_used'] = 0
            data['last_reset'] = today_start.isoformat()

        cooldown_until = data.get('cooldown_until')
        return UserStatus(
            user_id=user_id,
            daily_used=int(data.get('daily_used', 0)),
            daily_limit=int(data.get('daily_limit', 5)),
            cooldown_until=datetime.fromisoformat(cooldown_until) if cooldown_until else None,
            token_balance=self.get_balance(user_id),
            is_premium=data.get('is_premium') == 'true',
            last_reset=datetime.fromisoformat(data['last_reset'])
        )

    def _save_status(self, status: UserStatus):
        self.client.hset(self._get_status_key(status.user_id), mapping={
            "daily_used": status.daily_used,
            "daily_limit": status.daily_limit,
            "cooldown_until": status.cooldown_until.isoformat() if status.cooldown_until else "",
            "is_premium": "true" if status.is_premium else "false",
            "last_reset": status.last_reset.isoformat()
        })

    def record_analysis(self, user_id: str) -> UserStatus:
        if not self.use_redis:
            return super().record_analysis(user_id)
        
        status = self.get_user_status(user_id)
        
        # Increment daily_used if not premium
        if not status.is_premium:
            if status.daily_used < status.daily_limit:
                status.daily_used += 1
            
            # Set cooldown for everyone (including after free limit)
            from datetime import timedelta
            status.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=31)
            
        self._save_status(status)
        return status

    def set_premium(self, user_id: str, is_premium: bool) -> None:
        if not self.use_redis:
            return super().set_premium(user_id, is_premium)
        
        self.client.hset(self._get_status_key(user_id), "is_premium", "true" if is_premium else "false")
