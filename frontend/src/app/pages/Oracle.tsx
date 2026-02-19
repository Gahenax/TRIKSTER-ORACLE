import React, { useState } from 'react';
import { api } from '../lib/api';

interface OracleResponse {
    verdict: {
        value_detected: boolean;
        value_strength: string;
        confidence: string;
        reason_codes: string[];
    };
    text: {
        title: string;
        body_sections: { header: string; content: string }[];
    };
    chart: {
        enabled: boolean;
        data: any;
    };
    audit: {
        timing_ms: any;
        samples: number;
    };
    request_id?: string;
}

const OraclePage: React.FC = () => {
    const [primary, setPrimary] = useState('');
    const [opponent, setOpponent] = useState('');
    const [sport, setSport] = useState('FOOTBALL');
    const [mode, setMode] = useState('FAST');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<OracleResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const runAnalysis = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/oracle/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ primary, opponent, sport, mode })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Error en el Oráculo');
            setResult(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputStyle: React.CSSProperties = {
        width: '100%',
        padding: 'var(--space-md)',
        background: 'var(--color-bg-tertiary)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--color-text-primary)',
        fontFamily: 'var(--font-sans)',
        fontSize: 'var(--font-size-sm)',
    };

    return (
        <div className="section">
            <div className="container container-narrow">
                <div className="text-center mb-xl">
                    <h1>Trickster Oracle MVP</h1>
                    <p className="text-muted">Análisis probabilístico inteligente</p>
                </div>

                {/* Config Card */}
                <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                    <div className="card-header">
                        <h3 className="card-title">Configuración de Consulta</h3>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>
                                    Actor Principal
                                </label>
                                <input
                                    type="text"
                                    placeholder="Ej. Real Madrid"
                                    value={primary}
                                    onChange={e => setPrimary(e.target.value)}
                                    style={inputStyle}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>
                                    Oponente
                                </label>
                                <input
                                    type="text"
                                    placeholder="Ej. Barcelona"
                                    value={opponent}
                                    onChange={e => setOpponent(e.target.value)}
                                    style={inputStyle}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>
                                    Deporte
                                </label>
                                <select value={sport} onChange={e => setSport(e.target.value)} style={inputStyle}>
                                    <option value="FOOTBALL">Football</option>
                                    <option value="UFC">UFC</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-sm)', fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>
                                    Modo
                                </label>
                                <select value={mode} onChange={e => setMode(e.target.value)} style={inputStyle}>
                                    <option value="FAST">Fast (Lite)</option>
                                    <option value="ORACLE">Oracle (Deep)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="card-footer">
                        <button
                            onClick={runAnalysis}
                            disabled={loading || !primary || !opponent}
                            className="btn btn-primary"
                            style={{ width: '100%' }}
                        >
                            {loading ? 'Calculando...' : 'Ejecutar Oráculo'}
                        </button>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div style={{
                        padding: 'var(--space-md)',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-accent-danger)',
                        marginBottom: 'var(--space-xl)'
                    }}>
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {/* Results */}
                {result && (
                    <div>
                        {/* Verdict Card */}
                        <div className="card" style={{
                            borderLeft: `4px solid ${result.verdict.value_detected ? 'var(--color-accent-success)' : 'rgba(255, 255, 255, 0.2)'}`,
                            marginBottom: 'var(--space-xl)',
                        }}>
                            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <h3 className="card-title" style={{ margin: 0 }}>{result.text.title}</h3>
                                <span style={{
                                    padding: '2px 10px',
                                    borderRadius: 'var(--radius-full)',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    background: result.verdict.value_detected
                                        ? 'rgba(34, 197, 94, 0.15)'
                                        : 'rgba(255, 255, 255, 0.1)',
                                    color: result.verdict.value_detected
                                        ? 'var(--color-accent-success)'
                                        : 'var(--color-text-muted)',
                                }}>
                                    {result.verdict.value_strength}
                                </span>
                            </div>
                            <div className="card-body">
                                {result.text.body_sections.map((section, idx) => (
                                    <div key={idx} style={{ marginBottom: 'var(--space-lg)' }}>
                                        <h4 style={{
                                            fontSize: 'var(--font-size-xs)',
                                            textTransform: 'uppercase',
                                            letterSpacing: '1px',
                                            color: 'var(--color-text-muted)',
                                            marginBottom: 'var(--space-xs)'
                                        }}>
                                            {section.header}
                                        </h4>
                                        <p style={{ fontSize: 'var(--font-size-lg)', margin: 0 }}>
                                            {section.content}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Chart (text placeholder if enabled) */}
                        {result.chart.enabled && (
                            <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                                <div className="card-header">
                                    <h3 className="card-title">Distribución de Probabilidad</h3>
                                </div>
                                <div className="card-body" style={{
                                    height: '200px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: 'rgba(255, 255, 255, 0.02)',
                                    borderRadius: 'var(--radius-md)',
                                }}>
                                    <p style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                                        [Renderizado de Gráfico de Densidad: {result.chart.data?.series?.[0]?.name ?? 'N/A'}]
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Audit Footer */}
                        <div style={{
                            textAlign: 'center',
                            fontSize: 'var(--font-size-xs)',
                            color: 'var(--color-text-muted)',
                        }}>
                            Samples: {result.audit.samples} | Compute: {Math.round(result.audit.timing_ms?.compose ?? 0)}ms
                            {result.request_id && <> | ID: {result.request_id}</>}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default OraclePage;
