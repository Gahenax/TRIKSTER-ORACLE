import React from 'react';
import type { ScenarioV2 } from '../lib/types';

interface ScenarioGridProps {
    scenarios: ScenarioV2[];
}

const ScenarioGrid: React.FC<ScenarioGridProps> = ({ scenarios }) => {
    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--space-lg)',
            marginTop: 'var(--space-xl)'
        }}>
            {scenarios.map((s, i) => (
                <div key={i} className="card card-glass" style={{
                    padding: 'var(--space-lg)',
                    border: s.scenario_type === 'base' ? '1px solid var(--color-accent-primary)' : '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                    <div className="flex items-center justify-between mb-md">
                        <h4 style={{
                            margin: 0,
                            textTransform: 'uppercase',
                            letterSpacing: '1px',
                            color: s.scenario_type === 'base' ? 'var(--color-accent-primary)' : 'var(--color-text-main)'
                        }}>
                            {s.scenario_type}
                        </h4>
                        {s.scenario_type === 'base' && (
                            <span className="badge badge-success" style={{ fontSize: '10px' }}>RECOMMENDED</span>
                        )}
                    </div>

                    <div style={{ marginBottom: 'var(--space-md)' }}>
                        <div className="flex justify-between items-center mb-xs">
                            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Outcome Prob.</span>
                            <span style={{ fontWeight: 700 }}>{(s.prob_home * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{
                            height: '4px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            borderRadius: '2px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                height: '100%',
                                width: `${s.prob_home * 100}%`,
                                background: 'var(--color-accent-primary)'
                            }} />
                        </div>
                    </div>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 'var(--space-sm)',
                        fontSize: '11px',
                        color: 'var(--color-text-secondary)',
                        padding: 'var(--space-sm)',
                        background: 'rgba(0, 0, 0, 0.1)',
                        borderRadius: 'var(--radius-sm)'
                    }}>
                        <div>P25: {(s.percentiles.p25 * 100).toFixed(1)}%</div>
                        <div>P75: {(s.percentiles.p75 * 100).toFixed(1)}%</div>
                    </div>

                    <p style={{
                        fontSize: 'var(--font-size-xs)',
                        marginTop: 'var(--space-md)',
                        color: 'var(--color-text-muted)',
                        lineHeight: 1.4
                    }}>
                        {s.notes}
                    </p>
                </div>
            ))}
        </div>
    );
};

export default ScenarioGrid;
