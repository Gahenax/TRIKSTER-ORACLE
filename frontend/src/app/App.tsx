import { useState, useEffect, lazy, Suspense } from 'react';
import { api } from './lib/api';
import type { SimulationResult, SimulationResultV2, EventInput } from './lib/types';
import FooterDisclaimer from './components/FooterDisclaimer';

// Lazy load page components for better performance (code splitting)
const Home = lazy(() => import('./pages/Home'));
const Simulator = lazy(() => import('./pages/Simulator'));
const Result = lazy(() => import('./pages/Result'));
const ResultV2 = lazy(() => import('./pages/ResultV2'));
const Pricing = lazy(() => import('./pages/Pricing'));

type Page = 'home' | 'simulator' | 'result';

function App() {
    const [currentPage, setCurrentPage] = useState<Page>('home');
    const [engineVersion, setEngineVersion] = useState<'v1' | 'v2'>('v1');
    const [simulationResult, setSimulationResult] = useState<SimulationResult | SimulationResultV2 | null>(null);
    const [lastEvent, setLastEvent] = useState<EventInput | null>(null);
    const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
    const [userStatus, setUserStatus] = useState<any>(null); // Simplified for now
    const [userId] = useState<string>(`user_${Math.random().toString(36).substr(2, 9)}`);

    useEffect(() => {
        // Check backend health on mount
        api.checkHealth()
            .then(() => setIsBackendHealthy(true))
            .catch(() => setIsBackendHealthy(false));

        // Fetch user status
        api.getUserStatus(userId).then(setUserStatus);
    }, [userId]);

    const handleSimulate = (result: SimulationResult | SimulationResultV2, version: 'v1' | 'v2', event: EventInput) => {
        setSimulationResult(result);
        setEngineVersion(version);
        setLastEvent(event);

        if (version === 'v2') {
            setUserStatus((result as SimulationResultV2).user_status);
        }

        setCurrentPage('result');
    };

    const handleNavigateHome = () => {
        setCurrentPage('home');
        setSimulationResult(null);
    };

    const handleNavigateSimulator = () => {
        setCurrentPage('simulator');
    };

    const handleNavigatePricing = () => {
        setCurrentPage('pricing' as any);
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
                                onClick={handleNavigatePricing}
                                className="btn btn-secondary btn-sm"
                                style={{
                                    background: 'rgba(255, 215, 0, 0.1)',
                                    color: '#FFD700',
                                    border: '1px solid rgba(255, 215, 0, 0.3)'
                                }}
                            >
                                Get Premium
                            </button>
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

                            {userStatus && (
                                <span style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--space-md)' }}>
                                    <span>Tokens: <strong>{userStatus.token_balance}</strong></span>
                                    <span>Daily: <strong>{userStatus.daily_used} / {userStatus.daily_limit}</strong></span>
                                    {userStatus.is_premium && <span className="badge badge-premium">PREMIUM</span>}
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main style={{ flex: 1 }}>
                <Suspense fallback={
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: '400px',
                        color: 'var(--color-text-muted)'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                border: '3px solid var(--color-accent-primary)',
                                borderTopColor: 'transparent',
                                borderRadius: '50%',
                                margin: '0 auto var(--space-md)',
                                animation: 'spin 1s linear infinite'
                            }} />
                            <p>Loading...</p>
                        </div>
                    </div>
                }>
                    {currentPage === 'home' && (
                        <Home onNavigateSimulator={handleNavigateSimulator} />
                    )}
                    {currentPage === 'simulator' && (
                        <Simulator
                            onSimulate={handleSimulate}
                            isBackendHealthy={isBackendHealthy ?? false}
                            userStatus={userStatus}
                            userId={userId}
                        />
                    )}
                    {(currentPage as string) === 'pricing' && (
                        <Pricing
                            userStatus={userStatus}
                            onBack={handleNavigateSimulator}
                            userId={userId}
                            onUpdateStatus={setUserStatus}
                        />
                    )}
                    {currentPage === 'result' && simulationResult && (
                        engineVersion === 'v2' ? (
                            <ResultV2
                                result={simulationResult as SimulationResultV2}
                                event={lastEvent!}
                                onBack={handleNavigateSimulator}
                                onHome={handleNavigateHome}
                            />
                        ) : (
                            <Result
                                result={simulationResult as SimulationResult}
                                onBack={handleNavigateSimulator}
                                onHome={handleNavigateHome}
                            />
                        )
                    )}
                </Suspense>
            </main>

            {/* Footer */}
            <FooterDisclaimer />
        </div>
    );
}

export default App;
