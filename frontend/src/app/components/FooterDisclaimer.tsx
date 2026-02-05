export default function FooterDisclaimer() {
    return (
        <footer style={{
            background: 'var(--color-bg-secondary)',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            padding: 'var(--space-2xl) 0',
            marginTop: 'auto'
        }}>
            <div className="container">
                {/* Disclaimer */}
                <div className="card" style={{
                    background: 'rgba(239, 68, 68, 0.05)',
                    borderColor: 'rgba(239, 68, 68, 0.2)',
                    marginBottom: 'var(--space-xl)'
                }}>
                    <h4 style={{ color: 'var(--color-accent-danger)', marginBottom: 'var(--space-md)' }}>
                        ⚠️ Educational Tool — Not for Gambling
                    </h4>
                    <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', lineHeight: 1.7 }}>
                        <strong>Trickster Oracle is an educational platform for learning about probability and statistical analysis.</strong>
                        This system generates probabilistic estimates based on simplified models with inherent limitations.
                        It does NOT predict outcomes with certainty, does NOT recommend actions for financial gain, and is NOT
                        designed for gambling or betting purposes. Use this tool to understand how probability works, not to make
                        financial decisions. If you choose to use information from this system for any purpose, you do so at
                        your own risk and responsibility.
                    </p>
                </div>

                {/* Footer Links */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: 'var(--space-xl)',
                    marginBottom: 'var(--space-xl)'
                }}>
                    <div>
                        <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-md)' }}>
                            About
                        </h4>
                        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>
                            An open-source educational project for exploring probabilistic analysis through Monte Carlo
                            simulations, confidence intervals, and risk quantification.
                        </p>
                    </div>

                    <div>
                        <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-md)' }}>
                            Resources
                        </h4>
                        <ul style={{
                            listStyle: 'none',
                            padding: 0,
                            margin: 0,
                            fontSize: 'var(--font-size-sm)'
                        }}>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="https://github.com/Gahenax/TRIKSTER-ORACLE" target="_blank" rel="noopener noreferrer">
                                    GitHub Repository
                                </a>
                            </li>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="#" onClick={(e) => e.preventDefault()}>
                                    Documentation
                                </a>
                            </li>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="#" onClick={(e) => e.preventDefault()}>
                                    Methodology
                                </a>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-md)' }}>
                            Legal
                        </h4>
                        <ul style={{
                            listStyle: 'none',
                            padding: 0,
                            margin: 0,
                            fontSize: 'var(--font-size-sm)'
                        }}>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="#" onClick={(e) => e.preventDefault()}>
                                    Terms of Use
                                </a>
                            </li>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="#" onClick={(e) => e.preventDefault()}>
                                    Privacy Policy
                                </a>
                            </li>
                            <li style={{ marginBottom: 'var(--space-sm)' }}>
                                <a href="https://github.com/Gahenax/TRIKSTER-ORACLE/blob/master/LICENSE" target="_blank" rel="noopener noreferrer">
                                    License (MIT)
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Copyright */}
                <div style={{
                    paddingTop: 'var(--space-xl)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-muted)',
                    textAlign: 'center'
                }}>
                    <p style={{ margin: 0 }}>
                        © 2026 <a href="https://gahenaxaisolutions.com" target="_blank" rel="noopener noreferrer">
                            Gahenax AI Solutions
                        </a> — Trickster Oracle v0.1.0 (Demo)
                    </p>
                    <p style={{ margin: 'var(--space-sm) 0 0 0' }}>
                        Built with FastAPI, React, TypeScript, and Chart.js
                    </p>
                </div>
            </div>
        </footer>
    );
}
