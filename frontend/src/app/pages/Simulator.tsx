import { useState } from 'react';
import { api } from '../lib/api';
import type { EventInput, SimulationConfig, SimulationResult, SimulationResultV2 } from '../lib/types';

export interface SimulatorProps {
    onSimulate: (result: SimulationResult | SimulationResultV2, version: 'v1' | 'v2', event: EventInput) => void;
    isBackendHealthy: boolean;
    userStatus: any;
    userId: string;
}

export default function Simulator({ onSimulate, isBackendHealthy, userStatus, userId }: SimulatorProps) {
    const [loading, setLoading] = useState(false);
    const [engineVersion] = useState<'v1' | 'v2'>('v2');
    const [error, setError] = useState<string | null>(null);
    const [cooldownRemaining, setCooldownRemaining] = useState<number>(0);

    // Cooldown timer logic
    useState(() => {
        const interval = setInterval(() => {
            if (userStatus?.cooldown_until) {
                const remaining = Math.max(0, Math.ceil((new Date(userStatus.cooldown_until).getTime() - Date.now()) / 1000));
                setCooldownRemaining(remaining);
            }
        }, 1000);
        return () => clearInterval(interval);
    });

    const [event, setEvent] = useState<EventInput>({
        home_team: 'Barcelona',
        away_team: 'Real Madrid',
        home_rating: 2100,
        away_rating: 2050,
        home_advantage: 100,
        sport: 'football',
        event_id: `evt_${Date.now()}`
    });

    const [config, setConfig] = useState<SimulationConfig>({
        n_simulations: 1000,
        seed: undefined,
        ci_level: 0.95
    });

    const handleSimulate = async () => {
        setLoading(true);
        setError(null);

        try {
            if (engineVersion === 'v2') {
                const result = isBackendHealthy
                    ? await api.simulateV2(event, config, 'full_distribution', userId)
                    : await api.simulateMockV2(event, config);
                onSimulate(result, 'v2', event);
            } else {
                const result = isBackendHealthy
                    ? await api.simulate(event, config)
                    : await api.simulateMock(event, config);
                onSimulate(result, 'v1', event);
            }
        } catch (err: any) {
            setError(err.message || 'Simulation failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="simulator-page section">
            <div className="container container-narrow">
                <div className="text-center mb-xl">
                    <h1>Event Simulator</h1>
                    <p className="text-muted">
                        Configure event parameters and run a Monte Carlo simulation
                    </p>
                </div>

                {userStatus?.daily_used >= 4 && !userStatus.is_premium && (
                    <div style={{
                        padding: 'var(--space-md)',
                        background: 'rgba(255, 165, 0, 0.1)',
                        border: '1px solid rgba(255, 165, 0, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        color: '#FFA500',
                        marginBottom: 'var(--space-lg)',
                        textAlign: 'center',
                        fontSize: 'var(--font-size-sm)'
                    }}>
                        ⚠️ Warning: You have {userStatus.daily_limit - userStatus.daily_used} free analyses left for today.
                    </div>
                )}

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Event Configuration</h3>
                    </div>

                    <div className="card-body">
                        {/* Teams */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500 }}>
                                    Home Team
                                </label>
                                <input
                                    type="text"
                                    value={event.home_team}
                                    onChange={(e) => setEvent({ ...event, home_team: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: 'var(--space-md)',
                                        background: 'var(--color-bg-tertiary)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: 'var(--radius-md)',
                                        color: 'var(--color-text-primary)',
                                        fontFamily: 'var(--font-sans)'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500 }}>
                                    Away Team
                                </label>
                                <input
                                    type="text"
                                    value={event.away_team}
                                    onChange={(e) => setEvent({ ...event, away_team: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: 'var(--space-md)',
                                        background: 'var(--color-bg-tertiary)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: 'var(--radius-md)',
                                        color: 'var(--color-text-primary)',
                                        fontFamily: 'var(--font-sans)'
                                    }}
                                />
                            </div>
                        </div>

                        {/* Ratings */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500 }}>
                                    Home Rating (ELO)
                                </label>
                                <input
                                    type="number"
                                    value={event.home_rating}
                                    onChange={(e) => setEvent({ ...event, home_rating: Number(e.target.value) })}
                                    min={0}
                                    max={3000}
                                    style={{
                                        width: '100%',
                                        padding: 'var(--space-md)',
                                        background: 'var(--color-bg-tertiary)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: 'var(--radius-md)',
                                        color: 'var(--color-text-primary)',
                                        fontFamily: 'var(--font-sans)'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500 }}>
                                    Away Rating (ELO)
                                </label>
                                <input
                                    type="number"
                                    value={event.away_rating}
                                    onChange={(e) => setEvent({ ...event, away_rating: Number(e.target.value) })}
                                    min={0}
                                    max={3000}
                                    style={{
                                        width: '100%',
                                        padding: 'var(--space-md)',
                                        background: 'var(--color-bg-tertiary)',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: 'var(--radius-md)',
                                        color: 'var(--color-text-primary)',
                                        fontFamily: 'var(--font-sans)'
                                    }}
                                />
                            </div>
                        </div>

                        {/* Simulations */}
                        <div style={{ marginBottom: 'var(--space-lg)' }}>
                            <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500 }}>
                                Number of Simulations (100-1000)
                            </label>
                            <input
                                type="number"
                                value={config.n_simulations}
                                onChange={(e) => setConfig({ ...config, n_simulations: Number(e.target.value) })}
                                min={100}
                                max={1000}
                                step={100}
                                style={{
                                    width: '100%',
                                    padding: 'var(--space-md)',
                                    background: 'var(--color-bg-tertiary)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                    borderRadius: 'var(--radius-md)',
                                    color: 'var(--color-text-primary)',
                                    fontFamily: 'var(--font-sans)'
                                }}
                            />
                        </div>

                        {error && (
                            <div style={{
                                padding: 'var(--space-md)',
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                borderRadius: 'var(--radius-md)',
                                color: 'var(--color-accent-danger)',
                                marginBottom: 'var(--space-lg)'
                            }}>
                                {error}
                            </div>
                        )}
                    </div>

                    <div className="card-footer">
                        <button
                            onClick={handleSimulate}
                            disabled={loading || cooldownRemaining > 0}
                            className="btn btn-primary"
                            style={{ width: '100%', position: 'relative', overflow: 'hidden' }}
                        >
                            {loading ? (
                                <>
                                    <div className="loading-spinner" style={{ width: '20px', height: '20px' }} />
                                    Running Simulation...
                                </>
                            ) : cooldownRemaining > 0 ? (
                                <>
                                    Cooldown: {cooldownRemaining}s
                                    <div style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        left: 0,
                                        height: '4px',
                                        background: 'rgba(255,255,255,0.3)',
                                        width: `${(cooldownRemaining / 31) * 100}%`,
                                        transition: 'width 1s linear'
                                    }} />
                                </>
                            ) : (
                                'Run Simulation'
                            )}
                        </button>
                    </div>
                </div>

                {/* Info Card */}
                <div className="card card-glass mt-lg" style={{ background: 'rgba(99, 102, 241, 0.05)' }}>
                    <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                        <strong>Demo Mode:</strong> Maximum 1,000 simulations. The simulation uses a simplified ELO model
                        and does not account for injuries, form, weather, or other real-world factors. Results are for
                        educational purposes only.
                    </p>
                </div>
            </div>
        </div>
    );
}
