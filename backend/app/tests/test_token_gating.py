"""
Tests for M3: TOKEN_GATING_ANALYTICS_ACCESS

Verification requirements:
1. Deny when insufficient tokens
2. Allow and decrement when sufficient tokens
3. Idempotency protection (no double charge on retries)
4. Audit logs record all transactions
5. Refund functionality works
6. Free tier always accessible
"""

import pytest
from datetime import datetime

from app.core.tokens import (
    TokenLedger,
    FeatureTier,
    TokenTransaction,
    AccessDeniedError,
    FEATURE_COSTS,
    require_tokens,
    check_feature_access,
    get_ledger
)


@pytest.fixture
def ledger():
    """Create fresh ledger for each test"""
    return TokenLedger()


@pytest.fixture
def user_with_tokens(ledger):
    """User with 10 tokens"""
    ledger.set_balance("user_test", 10)
    return "user_test"


@pytest.fixture
def user_no_tokens(ledger):
    """User with 0 tokens"""
    ledger.set_balance("user_broke", 0)
    return "user_broke"


# TEST 1: Deny when insufficient tokens
def test_deny_insufficient_tokens(ledger, user_no_tokens):
    """
    M3 Test 1: Must deny access when user has insufficient tokens.
    
    Critical: No tokens = no premium features
    """
    user_id = user_no_tokens
    
    # Try to access feature requiring 2 tokens
    with pytest.raises(AccessDeniedError) as exc_info:
        ledger.consume_tokens(
            user_id=user_id,
            feature=FeatureTier.FULL_DISTRIBUTION
        )
    
    # Verify error details
    error = exc_info.value
    assert error.feature == FeatureTier.FULL_DISTRIBUTION
    assert error.required == 2
    assert error.available == 0
    
    # Balance should be unchanged
    assert ledger.get_balance(user_id) == 0
    
    # Transaction should be logged as denied
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 1
    assert history[0].status == "denied"
    assert history[0].cost == 2
    assert history[0].balance_after == 0  # No change
    
    print("TEST 1 PASSED: Insufficient tokens denied")


def test_deny_partial_tokens(ledger):
    """
    M3 Test 1b: Deny when tokens available but insufficient.
    """
    user_id = "user_partial"
    ledger.set_balance(user_id, 4)  # Only 4 tokens
    
    # Try to access 5-token feature
    with pytest.raises(AccessDeniedError):
        ledger.consume_tokens(
            user_id=user_id,
            feature=FeatureTier.DEEP_DIVE_EDUCATIONAL  # Costs 5
        )
    
    # Balance unchanged
    assert ledger.get_balance(user_id) == 4
    
    print("TEST 1b PASSED: Partial tokens insufficient")


# TEST 2: Allow and decrement when sufficient tokens
def test_allow_sufficient_tokens(ledger, user_with_tokens):
    """
    M3 Test 2: Must allow access and deduct tokens when sufficient.
    
    Critical: Proper token accounting
    """
    user_id = user_with_tokens
    initial_balance = ledger.get_balance(user_id)
    assert initial_balance == 10
    
    # Access feature costing 2 tokens
    transaction = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        event_id="event_123"
    )
    
    # Verify transaction
    assert transaction.user_id == user_id
    assert transaction.feature == FeatureTier.FULL_DISTRIBUTION
    assert transaction.cost == 2
    assert transaction.balance_before == 10
    assert transaction.balance_after == 8
    assert transaction.status == "success"
    assert transaction.event_id == "event_123"
    
    # Verify balance updated
    assert ledger.get_balance(user_id) == 8
    
    # Verify transaction logged
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 1
    assert history[0].transaction_id == transaction.transaction_id
    
    print("TEST 2 PASSED: Sufficient tokens allowed and deducted")


def test_multiple_consumptions(ledger, user_with_tokens):
    """
    M3 Test 2b: Multiple consumptions deduct correctly.
    """
    user_id = user_with_tokens
    
    # First consumption: 2 tokens
    tx1 = ledger.consume_tokens(user_id, FeatureTier.FULL_DISTRIBUTION)
    assert ledger.get_balance(user_id) == 8
    
    # Second consumption: 3 tokens
    tx2 = ledger.consume_tokens(user_id, FeatureTier.SCENARIO_EXTREMES)
    assert ledger.get_balance(user_id) == 5
    
    # Third consumption: 3 tokens
    tx3 = ledger.consume_tokens(user_id, FeatureTier.COMPARATIVE_ANALYSIS)
    assert ledger.get_balance(user_id) == 2
    
    # Fourth attempt: 5 tokens (should fail)
    with pytest.raises(AccessDeniedError):
        ledger.consume_tokens(user_id, FeatureTier.DEEP_DIVE_EDUCATIONAL)
    
    # Balance still 2
    assert ledger.get_balance(user_id) == 2
    
    # 3 successful + 1 denied = 4 transactions
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 4
    assert sum(1 for tx in history if tx.status == "success") == 3
    assert sum(1 for tx in history if tx.status == "denied") == 1
    
    print("TEST 2b PASSED: Multiple consumptions tracked correctly")


# TEST 3: Idempotency protection
def test_idempotency_no_double_charge(ledger, user_with_tokens):
    """
    M3 Test 3: Idempotency key prevents double charging.
    
    Critical: Network retries should not double-charge
    """
    user_id = user_with_tokens
    idempotency_key = "request_abc_123"
    
    # First request
    tx1 = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        idempotency_key=idempotency_key
    )
    
    assert ledger.get_balance(user_id) == 8  # 10 - 2
    
    # Retry with same idempotency key (simulates network retry)
    tx2 = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        idempotency_key=idempotency_key
    )
    
    # Should return same transaction
    assert tx2.transaction_id == tx1.transaction_id
    assert tx2.balance_before == 10
    assert tx2.balance_after == 8
    
    # Balance should NOT be charged twice
    assert ledger.get_balance(user_id) == 8  # Still 8, not 6
    
    # Only 1 transaction in history (not 2)
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 1
    
    print("TEST 3 PASSED: Idempotency prevents double charge")


def test_idempotency_different_keys(ledger, user_with_tokens):
    """
    M3 Test 3b: Different idempotency keys create separate transactions.
    """
    user_id = user_with_tokens
    
    # First request with key A
    tx1 = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        idempotency_key="key_A"
    )
    
    # Second request with key B
    tx2 = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        idempotency_key="key_B"
    )
    
    # Should be different transactions
    assert tx1.transaction_id != tx2.transaction_id
    
    # Both should be charged
    assert ledger.get_balance(user_id) == 6  # 10 - 2 - 2
    
    # 2 transactions in history
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 2
    
    print("TEST 3b PASSED: Different keys create separate transactions")


# TEST 4: Free tier always accessible
def test_free_tier_always_accessible(ledger, user_no_tokens):
    """
    M3 Test 4: Free tier (headline pick) always accessible.
    
    Critical: Education/accessibility - free tier has no barriers
    """
    user_id = user_no_tokens
    assert ledger.get_balance(user_id) == 0
    
    # Access free feature
    transaction = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.HEADLINE_PICK
    )
    
    # Should succeed
    assert transaction.status == "success"
    assert transaction.cost == 0
    assert transaction.balance_after == 0  # No change
    
    # Balance still 0
    assert ledger.get_balance(user_id) == 0
    
    print("TEST 4 PASSED: Free tier accessible without tokens")


# TEST 5: Audit logs
def test_audit_logs_all_transactions(ledger):
    """
    M3 Test 5: All transactions logged for audit trail.
    """
    user1 = "user_a"
    user2 = "user_b"
    
    ledger.set_balance(user1, 10)
    ledger.set_balance(user2, 5)
    
    # User 1: Success
    ledger.consume_tokens(user1, FeatureTier.FULL_DISTRIBUTION, event_id="event_1")
    
    # User 2: Success
    ledger.consume_tokens(user2, FeatureTier.SCENARIO_EXTREMES, event_id="event_2")
    
    # User 2: Denied (insufficient)
    with pytest.raises(AccessDeniedError):
        ledger.consume_tokens(user2, FeatureTier.DEEP_DIVE_EDUCATIONAL)
    
    # User 1: Success
    ledger.consume_tokens(user1, FeatureTier.COMPARATIVE_ANALYSIS, event_id="event_3")
    
    # Get all transactions
    all_txs = ledger.get_all_transactions()
    assert len(all_txs) == 4
    
    # Verify statuses
    success_txs = [tx for tx in all_txs if tx.status == "success"]
    denied_txs = [tx for tx in all_txs if tx.status == "denied"]
    
    assert len(success_txs) == 3
    assert len(denied_txs) == 1
    
    # Verify event IDs logged
    assert any(tx.event_id == "event_1" for tx in all_txs)
    assert any(tx.event_id == "event_2" for tx in all_txs)
    
    print("TEST 5 PASSED: Audit logs capture all transactions")


# TEST 6: Refund functionality
def test_refund_transaction(ledger, user_with_tokens):
    """
    M3 Test 6: Refund returns tokens and marks transaction.
    """
    user_id = user_with_tokens
    
    # Consume tokens
    tx = ledger.consume_tokens(
        user_id=user_id,
        feature=FeatureTier.DEEP_DIVE_EDUCATIONAL  # Costs 5
    )
    
    assert ledger.get_balance(user_id) == 5  # 10 - 5
    
    # Refund transaction
    refund_tx = ledger.refund_transaction(tx.transaction_id)
    
    # Verify refund transaction
    assert refund_tx.user_id == user_id
    assert refund_tx.cost == -5  # Negative = refund
    assert refund_tx.balance_before == 5
    assert refund_tx.balance_after == 10  # Restored
    assert refund_tx.status == "refunded"
    
    # Balance restored
    assert ledger.get_balance(user_id) == 10
    
    # Original transaction marked as refunded
    assert tx.status == "refunded"
    
    print("TEST 6 PASSED: Refund restores tokens")


def test_refund_idempotency(ledger, user_with_tokens):
    """
    M3 Test 6b: Cannot refund same transaction twice.
    """
    user_id = user_with_tokens
    
    # Consume and refund
    tx = ledger.consume_tokens(user_id, FeatureTier.FULL_DISTRIBUTION)
    ledger.refund_transaction(tx.transaction_id)
    
    # Try to refund again
    with pytest.raises(ValueError, match="already refunded"):
        ledger.refund_transaction(tx.transaction_id)
    
    print("TEST 6b PASSED: Double refund prevented")


# TEST 7: Check access (read-only)
def test_check_access_without_consuming(ledger, user_with_tokens):
    """
    M3 Test 7: check_access does not consume tokens.
    """
    user_id = user_with_tokens
    
    # Check access (should not consume)
    has_access = ledger.check_access(user_id, FeatureTier.FULL_DISTRIBUTION)
    assert has_access is True
    
    # Balance unchanged
    assert ledger.get_balance(user_id) == 10
    
    # No transactions logged
    history = ledger.get_transaction_history(user_id)
    assert len(history) == 0
    
    print("TEST 7 PASSED: Check access is read-only")


# TEST 8: Helper functions
def test_helper_require_tokens():
    """
    M3 Test 8: Helper function require_tokens works.
    """
    ledger = get_ledger()
    user_id = "helper_test_user"
    ledger.set_balance(user_id, 10)
    
    # Use helper
    tx = require_tokens(
        user_id=user_id,
        feature=FeatureTier.FULL_DISTRIBUTION,
        event_id="test_event"
    )
    
    assert tx.status == "success"
    assert ledger.get_balance(user_id) == 8
    
    print("TEST 8 PASSED: Helper functions work")


def test_helper_check_feature_access():
    """
    M3 Test 8b: Helper check_feature_access works.
    """
    ledger = get_ledger()
    user_id = "check_test_user"
    ledger.set_balance(user_id, 3)
    
    # Should have access to 2-token feature
    assert check_feature_access(user_id, FeatureTier.FULL_DISTRIBUTION) is True
    
    # Should NOT have access to 5-token feature
    assert check_feature_access(user_id, FeatureTier.DEEP_DIVE_EDUCATIONAL) is False
    
    print("TEST 8b PASSED: Check feature access helper works")


# TEST 9: Feature cost configuration
def test_feature_costs_defined():
    """
    M3 Test 9: All feature tiers have defined costs.
    """
    for tier in FeatureTier:
        assert tier in FEATURE_COSTS
        assert isinstance(FEATURE_COSTS[tier], int)
        assert FEATURE_COSTS[tier] >= 0
    
    # Verify specific costs per spec
    assert FEATURE_COSTS[FeatureTier.HEADLINE_PICK] == 0
    assert FEATURE_COSTS[FeatureTier.FULL_DISTRIBUTION] == 2
    assert FEATURE_COSTS[FeatureTier.SCENARIO_EXTREMES] == 3
    assert FEATURE_COSTS[FeatureTier.COMPARATIVE_ANALYSIS] == 3
    assert FEATURE_COSTS[FeatureTier.DEEP_DIVE_EDUCATIONAL] == 5
    
    print("TEST 9 PASSED: Feature costs match spec")


# TEST 10: Top-up functionality
def test_add_tokens_top_up(ledger):
    """
    M3 Test 10: Top-up adds tokens correctly.
    """
    user_id = "topup_user"
    ledger.set_balance(user_id, 5)
    
    # Top up 10 tokens
    new_balance = ledger.add_tokens(user_id, 10)
    
    assert new_balance == 15
    assert ledger.get_balance(user_id) == 15
    
    print("TEST 10 PASSED: Top-up works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
