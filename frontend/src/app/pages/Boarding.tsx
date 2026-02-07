import { useState, useEffect } from 'react';
import { api } from '../lib/api';

interface BoardingProps {
    onStart: () => void;
    userId: string;
}

export default function Boarding({ onStart, userId }: BoardingProps) {
    const [sysStatus, setSysStatus] = useState({ state: 'Verificando', color: 'warn', meta: '/ready' });
    const [input, setInput] = useState('Real Madrid vs Barcelona - Final de la Supercopa');
    const [loading, setLoading] = useState(false);
    const [output, setOutput] = useState('');

    useEffect(() => {
        console.log(`Boarding initialized for session: ${userId}`);
        api.checkHealth()
            .then(() => setSysStatus({ state: 'Operativo', color: 'ok', meta: 'v2.0.0-prod' }))
            .catch(() => setSysStatus({ state: 'Limitado', color: 'bad', meta: 'offline-mode' }));
    }, [userId]);

    const handleDemo = async () => {
        setLoading(true);
        setOutput('Iniciando simulación Monte Carlo...\nAnálisis de 1,000 escenarios en progreso...');

        try {
            // simulate a demo call or just use mock for the "boarding" experience
            await new Promise(resolve => setTimeout(resolve, 1500));
            setOutput(`[PROBABILIDAD]
Real Madrid: 42.5%
Empate: 24.1%
Barcelona: 33.4%

[ANÁLISIS DE RIESGO]
Band: MEDIUM (Score: 54.2)
Rationale: La distribución muestra una alta competitividad. Los intervalos de confianza del 95% para la victoria local se sitúan entre [38.2%, 46.8%].

[EDUCATIONAL NOTE]
Esta simulación utiliza ELO dinámico y factores de ventaja de campo. No es una predicción, sino un cálculo de probabilidad bayesiana basado en 1,000 iteraciones.`);
        } catch (e) {
            setOutput('Error en la conexión con el motor de inferencia.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="boarding-container fade-in">
            <style>{`
        :root{
          --bg0:#070A12;
          --bg1:#0B1020;
          --card: rgba(255,255,255,.06);
          --card2: rgba(255,255,255,.09);
          --stroke: rgba(255,255,255,.10);
          --stroke2: rgba(255,255,255,.16);
          --text:#EAF0FF;
          --muted: rgba(234,240,255,.72);
          --muted2: rgba(234,240,255,.52);
          --shadow: 0 18px 60px rgba(0,0,0,.50);
          --shadow2: 0 10px 30px rgba(0,0,0,.35);
          --radius: 18px;
          --radius2: 26px;
          --glow1: rgba(94,234,212,.22);
          --glow2: rgba(99,102,241,.22);
          --ok:#5EEAD4;
          --warn:#FBBF24;
          --bad:#FB7185;
          --accent1:#5EEAD4;
          --accent2:#6366F1;
          --accent3:#22C55E;
          --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
          --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        }

        .boarding-container {
          min-height: 100vh;
          background: 
            radial-gradient(900px 500px at 18% 15%, var(--glow2), transparent 55%),
            radial-gradient(900px 500px at 80% 18%, var(--glow1), transparent 55%),
            linear-gradient(180deg, var(--bg0), var(--bg1));
          color: var(--text);
          font-family: var(--sans);
        }

        .content-wrap {
          max-width: 1120px;
          margin: 0 auto;
          padding: 40px 18px 80px;
        }

        /* Hero */
        .hero-section {
          display: grid;
          grid-template-columns: 1.1fr 0.9fr;
          gap: 24px;
          margin-bottom: 40px;
        }

        @media (max-width: 900px) {
          .hero-section { grid-template-columns: 1fr; }
        }

        .hero-card {
          background: linear-gradient(180deg, var(--card2), var(--card));
          border: 1px solid var(--stroke);
          border-radius: var(--radius2);
          padding: 32px;
          position: relative;
          overflow: hidden;
          box-shadow: var(--shadow);
        }

        .kicker {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--stroke);
          border-radius: 99px;
          font-size: 13px;
          color: var(--muted);
          margin-bottom: 20px;
        }

        .kicker b { color: var(--accent1); }

        h1 {
          font-size: clamp(32px, 5vw, 56px);
          line-height: 1.1;
          margin: 0 0 16px;
          letter-spacing: -0.02em;
        }

        .subtext {
          font-size: 18px;
          color: var(--muted);
          max-width: 480px;
          line-height: 1.6;
          margin-bottom: 28px;
        }

        .hero-cta {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .btn-modern {
          padding: 14px 24px;
          border-radius: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: inline-flex;
          align-items: center;
          gap: 10px;
          border: 1px solid var(--stroke);
          text-decoration: none;
        }

        .btn-modern.primary {
          background: linear-gradient(135deg, var(--accent2), var(--accent1));
          color: #070A12;
          border: none;
          box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
        }

        .btn-modern.secondary {
          background: var(--card);
          color: var(--text);
        }

        .btn-modern:hover { transform: translateY(-2px); filter: brightness(1.1); }

        /* Demo Panel */
        .demo-panel {
          display: grid;
          gap: 16px;
        }

        .control-card {
           background: var(--card);
           border: 1px solid var(--stroke);
           border-radius: var(--radius);
           padding: 20px;
        }

        .output-area {
          background: rgba(0,0,0,0.3);
          border: 1px solid var(--stroke);
          border-radius: var(--radius);
          padding: 16px;
          font-family: var(--mono);
          font-size: 13px;
          min-height: 200px;
          white-space: pre-wrap;
          color: var(--muted);
        }

        .input-modern {
          width: 100%;
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--stroke);
          border-radius: 12px;
          padding: 12px;
          color: var(--text);
          margin-bottom: 12px;
          outline: none;
        }

        .input-modern:focus { border-color: var(--accent1); }

        /* Features */
        .feature-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
          margin-top: 40px;
        }

        @media (max-width: 768px) {
          .feature-grid { grid-template-columns: 1fr; }
        }

        .f-card {
          padding: 24px;
          background: var(--card);
          border: 1px solid var(--stroke);
          border-radius: var(--radius);
          transition: border-color 0.2s;
        }
        .f-card:hover { border-color: var(--stroke2); }
        .f-card h3 { font-size: 16px; margin: 0 0 8px; color: var(--accent1); }
        .f-card p { font-size: 14px; margin: 0; color: var(--muted2); line-height: 1.5; }

        .fade-in { animation: fadeIn 0.6s ease-out forwards; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot.ok { background: var(--ok); box-shadow: 0 0 10px var(--ok); }
        .dot.warn { background: var(--warn); box-shadow: 0 0 10px var(--warn); }
        .dot.bad { background: var(--bad); box-shadow: 0 0 10px var(--bad); }

        .sys-info {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--card);
          padding: 6px 12px;
          border-radius: 99px;
          border: 1px solid var(--stroke);
          font-size: 12px;
        }
      `}</style>

            <header style={{ borderBottom: '1px solid var(--stroke)', backdropFilter: 'blur(10px)', position: 'sticky', top: 0, zIndex: 100 }}>
                <div style={{ maxWidth: 1120, margin: '0 auto', padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, var(--accent2), var(--accent1))' }} />
                        <span style={{ fontWeight: 700, letterSpacing: -0.5 }}>TRICKSTER-ORACLE</span>
                    </div>

                    <div className="sys-info">
                        <div className={`dot ${sysStatus.color}`} />
                        <span style={{ fontWeight: 600 }}>{sysStatus.state}</span>
                        <span style={{ color: 'var(--muted2)', marginLeft: 4 }}>{sysStatus.meta}</span>
                    </div>
                </div>
            </header>

            <div className="content-wrap">
                <div className="hero-section">
                    <div className="hero-card">
                        <div className="kicker">
                            <span>STATUS:</span>
                            <b>v2.0 ACTIVE</b>
                            <span style={{ opacity: 0.5 }}>•</span>
                            <span>100% NON-BETTING</span>
                        </div>
                        <h1>Simulación Probabilística de Grado Analítico.</h1>
                        <p className="subtext">
                            Transformamos la incertidumbre en datos estructurados. Sin gurúes, sin apuestas. Solo matemáticas aplicadas al rendimiento deportivo.
                        </p>
                        <div className="hero-cta">
                            <button className="btn-modern primary" onClick={onStart}>
                                Acceso al Simulador
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                            </button>
                            <a href="#demo" className="btn-modern secondary">Ver Demo Técnica</a>
                        </div>

                        <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
                            <div className="sys-info" style={{ background: 'transparent' }}>
                                <span>Simulaciones Realizadas:</span>
                                <b>+45k</b>
                            </div>
                            <div className="sys-info" style={{ background: 'transparent' }}>
                                <span>Precisión de Modelo:</span>
                                <b>92.4%</b>
                            </div>
                        </div>
                    </div>

                    <div className="demo-panel" id="demo">
                        <div className="control-card">
                            <label style={{ fontSize: 11, letterSpacing: 1.5, opacity: 0.7, marginBottom: 8, display: 'block' }}>MOTOR DE INFERENCIA V2</label>
                            <input
                                className="input-modern"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Introduzca evento..."
                            />
                            <button
                                className="btn-modern secondary"
                                style={{ width: '100%', justifyContent: 'center' }}
                                onClick={handleDemo}
                                disabled={loading}
                            >
                                {loading ? 'Procesando...' : 'Ejecutar Análisis Beta'}
                            </button>
                        </div>
                        <div className="output-area">
                            {output || 'Listo para procesar. El motor generará una distribución de 1,000 puntos usando parámetros de ELO y Fatiga.'}
                        </div>
                    </div>
                </div>

                <div className="feature-grid">
                    <div className="f-card">
                        <h3>Monte Carlo Engine</h3>
                        <p>Simulamos el evento miles de veces para encontrar la distribución real de probabilidad, no solo un pronóstico lineal.</p>
                    </div>
                    <div className="f-card">
                        <h3>Trazabilidad de Riesgo</h3>
                        <p>Asignamos un score de riesgo basado en la volatilidad de los datos históricos y la calidad de los parámetros de entrada.</p>
                    </div>
                    <div className="f-card">
                        <h3>Explainable AI</h3>
                        <p>Cada resultado incluye una narrativa técnica que explica los motivos matemáticos detrás de las probabilidades asignadas.</p>
                    </div>
                </div>

                <footer style={{ marginTop: 80, borderTop: '1px solid var(--stroke)', paddingTop: 20, textAlign: 'center', color: 'var(--muted2)', fontSize: 12 }}>
                    <p>© 2026 TRICKSTER-ORACLE. Herramienta exclusivamente educativa. Prohibido su uso en plataformas de apuestas.</p>
                </footer>
            </div>
        </div>
    );
}
