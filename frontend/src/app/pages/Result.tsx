import type { SimulationResult } from '../lib/types';

interface ResultProps {
    result: SimulationResult;
    onBack: () => void;
    onHome: () => void;
}

export default function Result({ result, onBack, onHome }: ResultProps) {
    const { event, prob_home, prob_draw, prob_away, risk, explanation } = result;

    const getRiskColor = (band: string) => {
        switch (band) {
            case 'LOW': return 'var(--color-accent-success)';
            case 'MEDIUM': return 'var(--color-accent-warning)';
            case 'HIGH': return 'var(--color-accent-danger)';
            default: return 'var(--color-text-muted)';
        }
    };

    return (
        <div className="result-page section">
            <div className="container">
                {/* Header */}
                <div className="text-center mb-xl">
                    <h1>Simulation Results</h1>
                    <p className="text-muted">
                        {event.home_team} vs {event.away_team}
                    </p>
                </div>

                {/* Probabilities */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: 'var(--space-lg',
                    marginBottom: 'var(--space-2xl)'
                }}>
                    <div className="card card-glass text-center">
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>
                            HOME WIN
                        </div>
                        <div style={{ fontSize: 'var(--font-size-4xl)', fontWeight: 700, color: 'var(--color-accent-primary)' }}>
                            {(prob_home * 100).toFixed(1)}%
                        </div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-sm)' }}>
                            {event.home_team}
                        </div>
                    </div>

                    {prob_draw !== undefined && (
                        <div className="card card-glass text-center">
                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>
                                DRAW
                            </div>
                            <div style={{ fontSize: 'var(--font-size-4xl)', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                                {(prob_draw * 100).toFixed(1)}%
                            </div>
                        </div>
                    )}

                    <div className="card card-glass text-center">
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>
                            AWAY WIN
                        </div>
                        <div style={{ fontSize: 'var(--font-size-4xl)', fontWeight: 700, color: 'var(--color-accent-secondary)' }}>
                            {(prob_away * 100).toFixed(1)}%
                        </div>
                        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-sm)' }}>
                            {event.away_team}
                        </div>
                    </div>
                </div>

                {/* Risk Assessment */}
                <div className="card mb-lg">
                    <div className="card-header">
                        <h3 className="card-title">Risk Assessment</h3>
                    </div>
                    <div className="card-body">
                        <div className="flex items-center gap-lg mb-md">
                            <span className={`badge badge-risk-${risk.band.toLowerCase()}`}>
                                {risk.band}
                            </span>
                            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600, color: getRiskColor(risk.band) }}>
                                {risk.score.toFixed(0)}/100
                            </span>
                        </div>
                        <p style={{ margin: 0 }}>{risk.rationale}</p>
                    </div>
                </div>

                {/* Explanation */}
                <div className="card mb-lg">
                    <div className="card-header">
                        <h3 className="card-title">Summary</h3>
                    </div>
                    <div className="card-body">
                        <p style={{ fontSize: 'var(--font-size-lg)', lineHeight: 1.7 }}>
                            {explanation.summary}
                        </p>
                    </div>
                </div>

                {/* Scenarios */}
                {explanation.scenarios && explanation.scenarios.length > 0 && (
                    <div className="card mb-lg">
                        <div className="card-header">
                            <h3 className="card-title">Scenario Analysis</h3>
                        </div>
                        <div className="card-body">
                            {explanation.scenarios.map((scenario, idx) => (
                                <div key={idx} style={{ marginBottom: idx < explanation.scenarios.length - 1 ? 'var(--space-lg)' : 0 }}>
                                    <div className="flex items-center gap-md mb-sm">
                                        <h4 style={{ margin: 0 }}>{scenario.name}</h4>
                                        <code>{(scenario.probability * 100).toFixed(1)}%</code>
                                    </div>
                                    <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
                                        {scenario.description}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Caveats */}
                {explanation.caveats && explanation.caveats.length > 0 && (
                    <div className="card mb-lg" style={{ background: 'rgba(245, 158, 11, 0.05)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                        <div className="card-header">
                            <h3 className="card-title">Important Limitations</h3>
                        </div>
                        <div className="card-body">
                            <ul style={{ margin: 0, paddingLeft: 'var(--space-xl)' }}>
                                {explanation.caveats.map((caveat, idx) => (
                                    <li key={idx} style={{ marginBottom: 'var(--space-sm)', color: 'var(--color-text-secondary)' }}>
                                        {caveat}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-lg justify-center" style={{ marginTop: 'var(--space-2xl)' }}>
                    <button onClick={onBack} className="btn btn-secondary">
                        ← New Simulation
                    </button>
                    <button onClick={onHome} className="btn btn-outline">
                        Home
                    </button>
                </div>
            </div>
        </div>
    );
}
