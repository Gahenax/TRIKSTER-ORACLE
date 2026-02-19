import React from 'react';
import type { UserStatus } from '../lib/types';

interface TokenBadgeProps {
    userStatus: UserStatus | null;
    onRefresh?: () => void;
}

const TokenBadge: React.FC<TokenBadgeProps> = ({ userStatus, onRefresh }) => {
    if (!userStatus) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-sm)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
            }}>
                <div style={{
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    border: '2px solid rgba(255, 255, 255, 0.2)',
                    borderTopColor: 'var(--color-accent-primary)',
                    animation: 'spin 1s linear infinite',
                }} />
                Loading...
            </div>
        );
    }

    const { token_balance, daily_used, daily_limit, is_premium, cooldown_until } = userStatus;

    const isOnCooldown = cooldown_until && new Date(cooldown_until).getTime() > Date.now();
    const dailyRemaining = Math.max(0, daily_limit - daily_used);
    const isLowTokens = token_balance <= 2 && !is_premium;

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-md)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                cursor: onRefresh ? 'pointer' : 'default',
            }}
            onClick={onRefresh}
            title={onRefresh ? 'Click to refresh token balance' : undefined}
        >
            {/* Token Balance */}
            <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 10px',
                borderRadius: 'var(--radius-full)',
                background: isLowTokens
                    ? 'rgba(239, 68, 68, 0.1)'
                    : 'rgba(99, 102, 241, 0.1)',
                border: `1px solid ${isLowTokens ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`,
                color: isLowTokens ? 'var(--color-accent-danger)' : 'var(--color-accent-primary)',
                fontWeight: 600,
                transition: 'all 0.3s ease',
            }}>
                🪙 {token_balance}
            </span>

            {/* Daily Usage */}
            <span style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                color: dailyRemaining <= 1
                    ? 'var(--color-accent-warning)'
                    : 'var(--color-text-muted)',
            }}>
                📊 {daily_used}/{daily_limit}
            </span>

            {/* Cooldown Indicator */}
            {isOnCooldown && (
                <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    color: 'var(--color-accent-warning)',
                    fontSize: '10px',
                }}>
                    ⏳ Cooldown
                </span>
            )}

            {/* Premium Badge */}
            {is_premium && (
                <span style={{
                    padding: '1px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 165, 0, 0.2))',
                    border: '1px solid rgba(255, 215, 0, 0.4)',
                    color: '#FFD700',
                    fontWeight: 700,
                    fontSize: '10px',
                    letterSpacing: '0.5px',
                }}>
                    ★ PREMIUM
                </span>
            )}
        </div>
    );
};

export default TokenBadge;
