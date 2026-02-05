import { useState, useEffect } from 'react';
import { api } from './lib/api';
import Home from './pages/Home';
import Simulator from './pages/Simulator';
import Result from './pages/Result';
import type { SimulationResult } from './lib/types';
import FooterDisclaimer from './components/FooterDisclaimer';

type Page = 'home' | 'simulator' | 'result';

function App() {
    const [currentPage, setCurrentPage] = useState<Page>('home');
    const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
    const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

    useEffect(() => {
        // Check backend health on mount
        api.checkHealth()
            .then(() => setIsBackendHealthy(true))
            .catch(() => setIsBackendHealthy(false));
    }, []);

    const handleSimulate = (result: SimulationResult) => {
        setSimulationResult(result);
        setCurrentPage('result');
    };

    const handleNavigateHome = () => {
        setCurrentPage('home');
        setSimulationResult(null);
    };

    const handleNavigateSimulator = () => {
        setCurrentPage('simulator');
    };

    return (
        <div className="app">
            {/* Header */}
            <header className=" header" style={{
                background: 'var(--color-bg-glass)',
                backdropFilter: 'blur(20px)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                position: 'sticky',
                top: 0,
                zIndex: 'var(--z-sticky)',
                padding: 'var(--space-lg) 0'
            }}>
                <div className="container">
                    <div className="flex items-center justify-between">
                        <div
                            onClick={handleNavigateHome}
                            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}
                        >
                            <h1 className="text-gradient" style={{ margin: 0, fontSize: 'var(--font-size-2xl)' }}>
                                Trickster Oracle
                            </h1>
                            <span className="badge badge-demo">Demo</span>
                        </div>

                        <nav style={{ display: 'flex', gap: 'var(--space-lg)' }}>
                            <button
                                onClick={handleNavigateHome}
                                className="btn btn-secondary btn-sm"
                            >
                                Home
                            </button>
                            <button
                                onClick={handleNavigateSimulator}
                                className="btn btn-primary btn-sm"
                            >
                                Simulator
                            </button>
                        </nav>
                    </div>

                    {/* Backend Status Indicator */}
                    {isBackendHealthy !== null && (
                        <div style={{
                            marginTop: 'var(--space-sm)',
                            fontSize: 'var(--font-size-xs)',
                            color: 'var(--color-text-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--space-sm)'
                        }}>
                            <div style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: isBackendHealthy ? 'var(--color-accent-success)' : 'var(--color-accent-warning)'
                            }} />
                            {isBackendHealthy ? 'Backend Connected' : 'Backend Offline (Using Mock Data)'}
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main style={{ flex: 1 }}>
                {currentPage === 'home' && (
                    <Home onNavigateSimulator={handleNavigateSimulator} />
                )}
                {currentPage === 'simulator' && (
                    <Simulator
                        onSimulate={handleSimulate}
                        isBackendHealthy={isBackendHealthy ?? false}
                    />
                )}
                {currentPage === 'result' && simulationResult && (
                    <Result
                        result={simulationResult}
                        onBack={handleNavigateSimulator}
                        onHome={handleNavigateHome}
                    />
                )}
            </main>

            {/* Footer */}
            <FooterDisclaimer />
        </div>
    );
}

export default App;
