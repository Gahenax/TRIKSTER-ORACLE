from __future__ import annotations
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

class UserStatus(BaseModel):
    """Full user product status"""
    user_id: str
    daily_used: int = 0
    daily_limit: int = 5
    cooldown_until: Optional[datetime] = None
    token_balance: int = 0
    is_premium: bool = False
    last_reset: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))

class AccessDeniedError(Exception):
    """Raised when user has insufficient tokens"""
    def __init__(self, feature: FeatureTier, required: int, available: int):
        self.feature = feature
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient tokens for {feature.value}: required={required}, available={available}"
        )
