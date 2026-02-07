import React from 'react';

interface UncertaintyBadgesProps {
    volatility: number;
    dataQuality: number;
    decay: number;
}

const UncertaintyBadges: React.FC<UncertaintyBadgesProps> = ({ volatility, dataQuality, decay }) => {
    const getVolatilityLabel = (score: number) => {
        if (score < 30) return { label: 'Stable', color: 'var(--color-accent-success)' };
        if (score < 60) return { label: 'Moderate', color: 'var(--color-accent-warning)' };
        return { label: 'Volatile', color: 'var(--color-accent-danger)' };
    };

    const getQualityLabel = (score: number) => {
        if (score > 80) return { label: 'High Quality', color: 'var(--color-accent-success)' };
        if (score > 50) return { label: 'Standard', color: 'var(--color-accent-warning)' };
        return { label: 'Low Sample', color: 'var(--color-accent-danger)' };
    };

    const vol = getVolatilityLabel(volatility);
    const qual = getQualityLabel(dataQuality);

    return (
        <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
            <div className="badge-v2" style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${vol.color}`,
                padding: 'var(--space-xs) var(--space-md)',
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-sm)'
            }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Volatility:</span>
                <span style={{ fontWeight: 600, color: vol.color }}>{vol.label} ({volatility.toFixed(0)})</span>
            </div>

            <div className="badge-v2" style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${qual.color}`,
                padding: 'var(--space-xs) var(--space-md)',
                borderRadius: 'var(--radius-full)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-sm)'
            }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Data:</span>
                <span style={{ fontWeight: 600, color: qual.color }}>{qual.label} ({dataQuality.toFixed(0)}%)</span>
            </div>

            {decay > 0.05 && (
                <div className="badge-v2" style={{
                    background: 'rgba(255, 150, 0, 0.1)',
                    border: '1px solid var(--color-accent-warning)',
                    padding: 'var(--space-xs) var(--space-md)',
                    borderRadius: 'var(--radius-full)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-sm)'
                }}>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Decay:</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-accent-warning)' }}>-{(decay * 100).toFixed(1)}%/day</span>
                </div>
            )}
        </div>
    );
};

export default UncertaintyBadges;
