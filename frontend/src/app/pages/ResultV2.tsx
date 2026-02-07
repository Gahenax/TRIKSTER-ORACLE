import React from 'react';
import type { SimulationResultV2, EventInput } from '../lib/types';
import UncertaintyBadges from '../components/UncertaintyBadges';
import DistributionChart from '../components/DistributionChart';
import ScenarioGrid from '../components/ScenarioGrid';

interface ResultV2Props {
    result: SimulationResultV2;
    event: EventInput;
    onBack: () => void;
    onHome: () => void;
}

export default function ResultV2({ result, event, onBack, onHome }: ResultV2Props) {
    const { distribution, uncertainty, transaction_id } = result;

    return (
        <div className="result-page section" style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <div className="container">
                {/* Header Section */}
                <div style={{ marginBottom: 'var(--space-2xl)', textAlign: 'center' }}>
                    <div style={{ marginBottom: 'var(--space-md)' }}>
                        <UncertaintyBadges
                            volatility={uncertainty.volatility_score}
                            dataQuality={uncertainty.data_quality_index}
                            decay={uncertainty.confidence_decay}
                        />
                    </div>
                    <h1 style={{ marginBottom: 'var(--space-xs)' }}>Simulation Analytics v2.0</h1>
                    <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-lg)' }}>
                        Analysis of {event.home_team} vs {event.away_team}
                    </p>
                </div>

                {/* Primary Distribution Visualization */}
                <div className="card-v2" style={{
                    background: 'var(--color-bg-glass)',
                    padding: 'var(--space-2xl)',
                    borderRadius: 'var(--radius-xl)',
                    marginBottom: 'var(--space-xl)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    boxShadow: 'var(--shadow-lg)'
                }}>
                    <div className="flex justify-between items-start mb-xl">
                        <div>
                            <h3 style={{ margin: 0 }}>Probability Distribution</h3>
                            <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                Based on {distribution.n_sims.toLocaleString()} Monte Carlo iterations
                            </p>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 700, color: 'var(--color-accent-primary)' }}>
                                {(distribution.percentiles.p50 * 100).toFixed(1)}%
                            </div>
                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                                MEDIAN WIN PROBABILITY
                            </div>
                        </div>
                    </div>

                    <DistributionChart
                        percentiles={distribution.percentiles}
                        mean={distribution.mean}
                    />
                </div>

                {/* Scenario Analysis */}
                <div style={{ marginBottom: 'var(--space-2xl)' }}>
                    <div className="flex items-center gap-md mb-lg">
                        <h3 style={{ margin: 0 }}>Comparative Scenario Analysis</h3>
                        <span style={{
                            fontSize: '10px',
                            padding: '2px 8px',
                            background: 'rgba(255, 255, 255, 0.1)',
                            borderRadius: '4px',
                            color: 'var(--color-text-muted)'
                        }}>MULTI-SCENARIO V2</span>
                    </div>
                    <ScenarioGrid scenarios={distribution.scenarios} />
                </div>

                {/* Technical Footnote / Audit */}
                <div style={{
                    marginTop: 'var(--space-3xl)',
                    padding: 'var(--space-lg)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-muted)'
                }}>
                    <div>
                        <span style={{ marginRight: 'var(--space-lg)' }}>Transaction: <code>{transaction_id}</code></span>
                        <span>Model: <code>{distribution.model_version}</code></span>
                    </div>
                    <div>
                        <button onClick={onBack} className="btn btn-secondary btn-sm" style={{ marginRight: 'var(--space-md)' }}>
                            New Simulation
                        </button>
                        <button onClick={onHome} className="btn btn-outline btn-sm">
                            Home
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
