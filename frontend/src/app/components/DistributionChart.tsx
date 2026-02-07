import React from 'react';

interface DistributionChartProps {
    percentiles: {
        p5: number;
        p25: number;
        p50: number;
        p75: number;
        p95: number;
    };
    mean: number;
}

const DistributionChart: React.FC<DistributionChartProps> = ({ percentiles, mean }) => {
    // Normalizing values to percentage for CSS placement
    const toPct = (val: number) => `${Math.min(val * 100, 100)}%`;

    return (
        <div style={{ padding: 'var(--space-xl) 0' }}>
            <div style={{
                height: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 'var(--radius-full)',
                position: 'relative',
                marginBottom: 'var(--space-2xl)'
            }}>
                {/* Confidence Range P5 - P95 (Outer shadow area) */}
                <div style={{
                    position: 'absolute',
                    left: toPct(percentiles.p5),
                    right: `${100 - parseFloat(toPct(percentiles.p95))}%`,
                    height: '100%',
                    background: 'rgba(var(--color-accent-primary-rgb), 0.1)',
                    borderRadius: 'var(--radius-full)',
                    border: '1px dashed rgba(255, 255, 255, 0.2)'
                }} />

                {/* Common Range P25 - P75 (Focus area) */}
                <div style={{
                    position: 'absolute',
                    left: toPct(percentiles.p25),
                    right: `${100 - parseFloat(toPct(percentiles.p75))}%`,
                    height: '24px',
                    top: '-8px',
                    background: 'linear-gradient(90deg, var(--color-accent-primary), var(--color-accent-secondary))',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <span style={{ fontSize: '10px', color: '#fff', fontWeight: 700 }}>50% CONFIDENCE</span>
                </div>

                {/* Median Indicator (P50) */}
                <div style={{
                    position: 'absolute',
                    left: toPct(percentiles.p50),
                    top: '-12px',
                    height: '32px',
                    width: '2px',
                    background: '#fff',
                    zIndex: 2,
                    boxShadow: '0 0 10px #fff'
                }}>
                    <div style={{
                        position: 'absolute',
                        top: '-25px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: '12px',
                        fontWeight: 700,
                        whiteSpace: 'nowrap'
                    }}>
                        MEDIAN: {(percentiles.p50 * 100).toFixed(1)}%
                    </div>
                </div>

                {/* Markers for P5 and P95 */}
                {[percentiles.p5, percentiles.p95].map((p, i) => (
                    <div key={i} style={{
                        position: 'absolute',
                        left: toPct(p),
                        top: '12px',
                        fontSize: '10px',
                        color: 'var(--color-text-muted)',
                        transform: 'translateX(-50%)'
                    }}>
                        P{i === 0 ? '5' : '95'}: {(p * 100).toFixed(0)}%
                    </div>
                ))}
            </div>

            <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
                textAlign: 'center',
                fontStyle: 'italic',
                marginTop: 'var(--space-md)'
            }}>
                Mean outcome: {(mean * 100).toFixed(1)}% probability across {percentiles.p95 - percentiles.p5 > 0.4 ? 'high' : 'low'} variance spread.
            </p>
        </div>
    );
};

export default DistributionChart;
