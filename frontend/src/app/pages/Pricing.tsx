import { useState } from 'react';
import { UserStatus } from '../lib/types';

interface PricingProps {
    userStatus: UserStatus;
    onBack: () => void;
    userId: string;
    onUpdateStatus: (status: UserStatus) => void;
}

export default function Pricing({ userStatus, onBack, userId, onUpdateStatus }: PricingProps) {
    const [loading, setLoading] = useState<string | null>(null);

    const handlePurchase = async (type: 'tokens' | 'premium', amount?: number) => {
        setLoading(type === 'tokens' ? `tokens_${amount}` : 'premium');

        try {
            // Mock API calls for purchase
            if (type === 'tokens' && amount) {
                const response = await fetch(`/api/v2/tokens/topup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, amount })
                });
                if (response.ok) {
                    const data = await response.json();
                    onUpdateStatus({ ...userStatus, token_balance: data.balance });
                }
            } else if (type === 'premium') {
                const response = await fetch(`/api/v2/me/premium`, {
                    method: 'POST',
                    headers: { 'X-User-ID': userId }
                });
                if (response.ok) {
                    const data = await response.json();
                    onUpdateStatus(data);
                }
            }
            alert('Success! Your account has been updated.');
        } catch (err) {
            console.error(err);
            alert('Mock purchase failed. (This is a demo)');
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="container" style={{ padding: 'var(--space-2xl) 0' }}>
            <div className="text-center mb-2xl">
                <h1 className="text-gradient" style={{ fontSize: 'var(--font-size-3xl)' }}>Go Premium</h1>
                <p className="text-muted">Unleash the full power of the Trickster Oracle engine.</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-xl)' }}>
                {/* Free Tier Card */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                    <div className="card-header">
                        <h3 className="card-title">Free Daily</h3>
                        <p className="text-muted">For casual observers</p>
                    </div>
                    <div className="card-body" style={{ flex: 1 }}>
                        <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'bold', marginBottom: 'var(--space-md)' }}>$0 <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>/ month</span></div>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                            <li>✅ 5 analyses per day</li>
                            <li>✅ V2 Analytics Engine</li>
                            <li>⏳ 31s cooldown between runs</li>
                        </ul>
                    </div>
                    <div className="card-footer">
                        <button className="btn btn-secondary" style={{ width: '100%' }} disabled>Your Current Plan</button>
                    </div>
                </div>

                {/* Token Packs Card */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', border: '1px solid var(--color-accent-primary)' }}>
                    <div className="card-header">
                        <h3 className="card-title">Token Packs</h3>
                        <p className="text-muted">Pay as you go</p>
                    </div>
                    <div className="card-body" style={{ flex: 1 }}>
                        <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'bold', marginBottom: 'var(--space-md)' }}>From $2.99</div>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', marginBottom: 'var(--space-lg)' }}>
                            <li>✅ No daily limits</li>
                            <li>✅ Same-day usage</li>
                            <li>✅ Lifetime validity</li>
                        </ul>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                            <button
                                onClick={() => handlePurchase('tokens', 10)}
                                disabled={!!loading}
                                className="btn btn-primary btn-sm"
                            >
                                10 Tokens - $2.99
                            </button>
                            <button
                                onClick={() => handlePurchase('tokens', 30)}
                                disabled={!!loading}
                                className="btn btn-primary btn-sm"
                            >
                                30 Tokens - $7.99
                            </button>
                            <button
                                onClick={() => handlePurchase('tokens', 100)}
                                disabled={!!loading}
                                className="btn btn-primary btn-sm"
                            >
                                100 Tokens - $19.99
                            </button>
                        </div>
                    </div>
                </div>

                {/* Premium Card */}
                <div className="card" style={{
                    display: 'flex',
                    flexDirection: 'column',
                    background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.05) 0%, rgba(255, 215, 0, 0.15) 100%)',
                    border: '1px solid rgba(255, 215, 0, 0.3)'
                }}>
                    <div className="card-header">
                        <div className="badge badge-premium" style={{ marginBottom: 'var(--space-sm)' }}>BEST VALUE</div>
                        <h3 className="card-title" style={{ color: '#FFD700' }}>Pro Subscription</h3>
                        <p className="text-muted">Unlimited access</p>
                    </div>
                    <div className="card-body" style={{ flex: 1 }}>
                        <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'bold', marginBottom: 'var(--space-md)', color: '#FFD700' }}>$9.99 <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>/ month</span></div>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                            <li>🚀 <strong>ZERO</strong> cooldown</li>
                            <li>🚀 <strong>UNLIMITED</strong> daily analysis</li>
                            <li>🚀 Priority engine processing</li>
                            <li>🚀 Advanced Scenarios unlocked</li>
                        </ul>
                    </div>
                    <div className="card-footer">
                        <button
                            onClick={() => handlePurchase('premium')}
                            disabled={!!loading || userStatus.is_premium}
                            className="btn btn-primary"
                            style={{
                                width: '100%',
                                background: '#FFD700',
                                color: '#000',
                                fontWeight: 'bold'
                            }}
                        >
                            {userStatus.is_premium ? 'Premium Active' : 'Subscribe Now'}
                        </button>
                    </div>
                </div>
            </div>

            <div className="text-center" style={{ marginTop: 'var(--space-2xl)' }}>
                <button onClick={onBack} className="btn btn-secondary">
                    Back to Simulator
                </button>
            </div>
        </div>
    );
}
