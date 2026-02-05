interface HomeProps {
    onNavigateSimulator: () => void;
}

export default function Home({ onNavigateSimulator }: HomeProps) {
    return (
        <div className="home-page">
            {/* Hero Section */}
            <section className="section" style={{ paddingTop: 'var(--space-3xl)' }}>
                <div className="container text-center">
                    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                        <h1 style={{
                            fontSize: 'clamp(2rem, 5vw, 4rem)',
                            marginBottom: 'var(--space-xl)',
                            lineHeight: 1.1
                        }}>
                            Understand <span className="text-gradient">Probability</span>,
                            <br />
                            Not Predictions
                        </h1>

                        <p style={{
                            fontSize: 'var(--font-size-xl)',
                            color: 'var(--color-text-secondary)',
                            marginBottom: 'var(--space-2xl)',
                            lineHeight: 1.6
                        }}>
                            An educational platform for exploring probabilistic scenarios in sports events
                            using Monte Carlo simulations, confidence intervals, and risk analysis.
                        </p>

                        <div className="flex gap-lg justify-center" style={{ flexWrap: 'wrap' }}>
                            <button
                                onClick={onNavigateSimulator}
                                className="btn btn-primary btn-lg"
                            >
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M10 3v14m7-7H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                </svg>
                                Start Simulation
                            </button>

                            <button className="btn btn-secondary btn-lg">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M6 10h8M10 6v8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    <rect x="2" y="2" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none" />
                                </svg>
                                Learn More
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="section container">
                <h2 className="text-center mb-xl">What You'll Learn</h2>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: 'var(--space-xl)',
                    marginTop: 'var(--space-2xl)'
                }}>
                    {/* Feature 1 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'var(--gradient-primary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 2v20M2 12h20" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                                <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="2" fill="none" />
                            </svg>
                        </div>
                        <h3>Monte Carlo Simulation</h3>
                        <p>
                            Run thousands of probabilistic scenarios to understand the distribution of outcomes,
                            not just a single prediction.
                        </p>
                    </div>

                    {/* Feature 2 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'var(--gradient-success)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M3 13h4l3 6 4-12 3 6h4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Confidence Intervals</h3>
                        <p>
                            Quantify uncertainty with CI ranges that show not just probabilities,
                            but how confident we can be in those estimates.
                        </p>
                    </div>

                    {/* Feature 3 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'var(--gradient-accent)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 9v6m0 0l-3-3m3 3l3-3" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="2" fill="none" />
                            </svg>
                        </div>
                        <h3>Risk Assessment</h3>
                        <p>
                            Evaluate volatility with clear risk bands (Low/Medium/High)
                            and understand what drives uncertainty.
                        </p>
                    </div>

                    {/* Feature 4 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M9 12h6m-3-3v6" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                                <rect x="3" y="3" width="18" height="18" rx="2" stroke="white" strokeWidth="2" fill="none" />
                            </svg>
                        </div>
                        <h3>Sensitivity Analysis</h3>
                        <p>
                            Explore "what-if" scenarios to see which factors have the biggest
                            impact on probabilities.
                        </p>
                    </div>

                    {/* Feature 5 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'linear-gradient(135deg, #f59e0b 0%, #eab308 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Explainability</h3>
                        <p>
                            Get human-readable summaries, scenario analyses, and clear caveats
                            about model limitations.
                        </p>
                    </div>

                    {/* Feature 6 */}
                    <div className="card card-glass">
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: 'var(--radius-lg)',
                            background: 'linear-gradient(135deg, #a855f7 0%, #d946ef 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-lg)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 15v.01M12 12v-6m0 0a3 3 0 100-6 3 3 0 000 6z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Open & Educational</h3>
                        <p>
                            Fully transparent methodology. No black boxes, no hidden agendas.
                            Learn how probability actually works.
                        </p>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="section container">
                <div className="card card-glass text-center" style={{
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    padding: 'var(--space-3xl)'
                }}>
                    <h2 className="mb-lg">Ready to Explore Probability?</h2>
                    <p style={{
                        fontSize: 'var(--font-size-lg)',
                        maxWidth: '600px',
                        margin: '0 auto var(--space-2xl)'
                    }}>
                        Run your first Monte Carlo simulation and see how probability distributions,
                        confidence intervals, and risk analysis work in practice.
                    </p>
                    <button
                        onClick={onNavigateSimulator}
                        className="btn btn-primary btn-lg"
                    >
                        Launch Simulator
                    </button>
                </div>
            </section>
        </div>
    );
}
