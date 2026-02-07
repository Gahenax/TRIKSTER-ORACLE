import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
import redis
from app.core.token_types import TokenTransaction, FeatureTier, UserStatus


logger = logging.getLogger(__name__)

class RedisTokenLedger:
    """
    Redis-backed token ledger for production persistence.
    Uses Redis hashes for balances and lists for transaction history.
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, url=None):
        self.use_redis = False
        try:
            if url:
                self.client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
            else:
                self.client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db, 
                    password=password, 
                    decode_responses=True,
                    socket_connect_timeout=2
                )
            self.client.ping()
            self.use_redis = True
            logger.info(f"Connected to Redis for TokenLedger at {host}:{port}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to in-memory TokenLedger.")
            # We'll use a simple in-memory store if Redis is unavailable
            self._balances = {}
            self._transactions = []
            self._idempotency_cache = {}
            self._user_statuses = {}

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
            return self._balances.get(user_id, 0)
        
        balance = self.client.get(self._get_balance_key(user_id))
        return int(balance) if balance else 0

    def set_balance(self, user_id: str, balance: int) -> None:
        if not self.use_redis:
            self._balances[user_id] = balance
            return
        
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        self.client.set(self._get_balance_key(user_id), balance)

    def add_tokens(self, user_id: str, amount: int) -> int:
        if not self.use_redis:
            current = self.get_balance(user_id)
            self._balances[user_id] = current + amount
            return self._balances[user_id]
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        new_balance = self.client.incrby(self._get_balance_key(user_id), amount)
        return new_balance

    def check_access(self, user_id: str, feature: FeatureTier) -> bool:
        from app.core.token_types import FEATURE_COSTS
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
        if not self.use_redis:
            # Simple in-memory logic
            if idempotency_key and idempotency_key in self._idempotency_cache:
                tx_id = self._idempotency_cache[idempotency_key]
                for tx in self._transactions:
                    if tx.transaction_id == tx_id: return tx
            
            from app.core.token_types import FEATURE_COSTS, AccessDeniedError
            required = FEATURE_COSTS[feature]
            available = self.get_balance(user_id)
            
            if available < required:
                raise AccessDeniedError(feature, required, available)
            
            new_balance = available - required
            self._balances[user_id] = new_balance
            tx = TokenTransaction(user_id=user_id, feature=feature, cost=required, balance_before=available, balance_after=new_balance, event_id=event_id, idempotency_key=idempotency_key)
            self._transactions.append(tx)
            if idempotency_key: self._idempotency_cache[idempotency_key] = tx.transaction_id
            return tx

        # Redis logic
        if idempotency_key:
            cached_tx = self.client.get(self._get_idempotency_key(idempotency_key))
            if cached_tx:
                return TokenTransaction.model_validate_json(cached_tx)

        from app.core.token_types import FEATURE_COSTS
        required = FEATURE_COSTS[feature]
        
        current = self.get_balance(user_id)
        if current < required:
            from app.core.token_types import AccessDeniedError
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
        
        tx_json = transaction.model_dump_json()
        self.client.lpush(self._get_tx_key(user_id), tx_json)
        self.client.ltrim(self._get_tx_key(user_id), 0, 99)
        
        if idempotency_key:
            self.client.setex(self._get_idempotency_key(idempotency_key), 86400, tx_json)

        return transaction

    def get_transaction_history(self, user_id: str, limit: int = 100) -> List[TokenTransaction]:
        if not self.use_redis:
            return [tx for tx in self._transactions if tx.user_id == user_id][:limit]
        
        txs_json = self.client.lrange(self._get_tx_key(user_id), 0, limit - 1)
        return [TokenTransaction.model_validate_json(tx) for tx in txs_json]

    def get_all_transactions(self) -> List[TokenTransaction]:
        if not self.use_redis:
            return self._transactions
        
        # NOTE: In production with Redis, getting ALL transactions across ALL users
        # is expensive. This is a simplified version for small scale.
        # Ideally would use a separate global audit key.
        return self._transactions if hasattr(self, "_transactions") else []

    def get_user_status(self, user_id: str) -> UserStatus:
        if not self.use_redis:
            status = self._user_statuses.get(user_id)
            if not status:
                status = UserStatus(user_id=user_id, token_balance=self.get_balance(user_id))
                self._user_statuses[user_id] = status
            return status

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        data = self.client.hgetall(self._get_status_key(user_id))
        
        if not data:
            status = UserStatus(user_id=user_id, token_balance=self.get_balance(user_id), last_reset=today_start)
            self._save_status(status)
            return status

        # Check reset
        last_reset = datetime.fromisoformat(data['last_reset'].replace('Z', '+00:00'))
        if last_reset < today_start:
            self.client.hset(self._get_status_key(user_id), mapping={"daily_used": 0, "last_reset": today_start.isoformat()})
            data['daily_used'] = 0

        return UserStatus(
            user_id=user_id,
            daily_used=int(data.get('daily_used', 0)),
            daily_limit=int(data.get('daily_limit', 5)),
            cooldown_until=datetime.fromisoformat(data['cooldown_until'].replace('Z', '+00:00')) if data.get('cooldown_until') else None,
            token_balance=self.get_balance(user_id),
            is_premium=data.get('is_premium') == 'true',
            last_reset=today_start
        )

    def _save_status(self, status: UserStatus):
        if not self.use_redis: return
        self.client.hset(self._get_status_key(status.user_id), mapping={
            "daily_used": status.daily_used,
            "daily_limit": status.daily_limit,
            "cooldown_until": status.cooldown_until.isoformat() if status.cooldown_until else "",
            "is_premium": "true" if status.is_premium else "false",
            "last_reset": status.last_reset.isoformat()
        })

    def record_analysis(self, user_id: str) -> UserStatus:
        status = self.get_user_status(user_id)
        if not status.is_premium:
            if status.daily_used < status.daily_limit: status.daily_used += 1
            status.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=31)
        self._save_status(status)
        return status

    def set_premium(self, user_id: str, is_premium: bool) -> None:
        if not self.use_redis:
            status = self.get_user_status(user_id)
            status.is_premium = is_premium
            return
        self.client.hset(self._get_status_key(user_id), "is_premium", "true" if is_premium else "false")
