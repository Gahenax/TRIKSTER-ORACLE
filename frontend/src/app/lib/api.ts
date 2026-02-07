/**
 * API Client for Trickster Oracle Backend
 * Handles all HTTP communication with the FastAPI backend
 */

import type {
    EventInput,
    SimulationConfig,
    SimulationResult,
    SimulationResultV2,
    HealthResponse,
    VersionResponse,
    ErrorResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class TricksterAPI {
    async checkHealth(): Promise<HealthResponse> {
        const response = await fetch(`${API_BASE_URL}/v2/health`);
        if (!response.ok) {
            // Fallback to v1 health if v2 is not yet deployed
            const v1Response = await fetch(`${API_BASE_URL}/health`);
            if (!v1Response.ok) throw new Error('Backend health check failed');
            return v1Response.json();
        }
        return response.json();
    }

    async getVersion(): Promise<VersionResponse> {
        const response = await fetch(`${API_BASE_URL}/version`);
        if (!response.ok) {
            throw new Error('Failed to fetch API version');
        }
        return response.json();
    }

    /**
     * Simulation V2 - Depth-based Analytics
     */
    async simulateV2(
        event: EventInput,
        config: SimulationConfig,
        depth: string = 'full_distribution',
        userId: string = 'demo_user'
    ): Promise<SimulationResultV2> {
        const response = await fetch(`${API_BASE_URL}/v2/simulate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId,
                'X-Idempotency-Key': `req_${Date.now()}`
            },
            body: JSON.stringify({
                ...event,
                depth,
                config,
            }),
        });

        if (!response.ok) {
            // Handle 402 Payment Required for tokens
            if (response.status === 402) {
                throw new Error('Insufficient tokens for this analysis depth.');
            }
            const error: ErrorResponse = await response.json();
            throw new Error(error.message || 'Simulation v2 failed');
        }

        return response.json();
    }

    async simulate(
        event: EventInput,
        config: SimulationConfig
    ): Promise<SimulationResult> {
        const response = await fetch(`${API_BASE_URL}/v1/simulate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event,
                config,
            }),
        });

        if (!response.ok) {
            const error: ErrorResponse = await response.json();
            throw new Error(error.message || 'Simulation failed');
        }

        return response.json();
    }

    // Mock simulation for development (when backend is not running)
    async simulateMock(
        event: EventInput,
        config: SimulationConfig
    ): Promise<SimulationResult> {
        // Simulate network delay
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Generate mock data
        const mockResult: SimulationResult = {
            event,
            config,
            prob_home: 0.55,
            prob_draw: 0.25,
            prob_away: 0.20,
            distribution: {
                bins: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                frequencies: [0, 5, 12, 28, 45, 68, 52, 30, 15, 5, 0],
            },
            confidence_intervals: {
                '95': { lower: 0.50, upper: 0.60 },
                '99': { lower: 0.48, upper: 0.62 },
            },
            risk: {
                score: 35.0,
                band: 'MEDIUM',
                rationale:
                    'Moderate uncertainty based on rating differential and simulation variance',
            },
            explanation: {
                summary: `The simulation estimates a probability of 55% that ${event.home_team} will win, based on the provided ratings. The risk assessment is MEDIUM (35/100), with moderate uncertainty. These are statistical estimates based on limited historical data and a simplified model—not predictions of the actual outcome.`,
                scenarios: [
                    {
                        name: 'Most Probable Outcome',
                        probability: 0.55,
                        description: `${event.home_team} win is the most likely result with estimated probability of 55%. This is based on the rating differential and home advantage parameters.`,
                    },
                    {
                        name: 'Surprise Scenario',
                        probability: 0.20,
                        description: `${event.away_team} win has the lowest estimated probability (20%), but remains a plausible outcome.`,
                    },
                ],
                caveats: [
                    'This analysis uses a simplified ELO-based model and does not account for injuries, team news, weather conditions, tactical changes, or motivation factors.',
                    'The simulation is based on 1,000 Monte Carlo iterations. While this provides statistical robustness, the underlying model has inherent limitations.',
                    'This is an educational tool for understanding probability and risk analysis. It is not designed for gambling decisions.',
                ],
                sensitivity: [
                    {
                        factor_name: 'Home Team Rating (+50 ELO)',
                        delta_probability: 4.8,
                        impact_level: 'MEDIUM',
                    },
                    {
                        factor_name: 'Home Advantage (+50 points)',
                        delta_probability: 3.2,
                        impact_level: 'MEDIUM',
                    },
                ],
            },
            model_version: '0.1.0',
            execution_time_ms: 142.5,
            cache_hit: false,
        };

        return mockResult;
    }
    // Mock simulation for development v2
    async simulateMockV2(
        event: EventInput,
        config: SimulationConfig
    ): Promise<SimulationResultV2> {
        await new Promise((resolve) => setTimeout(resolve, 1200));

        return {
            distribution: {
                sport: event.sport,
                event_id: event.event_id,
                market: 'match_winner',
                model_version: '2.0.0-beta',
                n_sims: config.n_simulations,
                ci_level: config.ci_level,
                percentiles: {
                    p5: 0.380,
                    p25: 0.495,
                    p50: 0.565,
                    p75: 0.640,
                    p95: 0.745
                },
                mean: 0.568,
                stdev: 0.112,
                skew: -0.12,
                kurtosis: 0.05,
                scenarios: [
                    {
                        scenario_type: 'conservative',
                        parameters: { "variance_multiplier": 1.3 },
                        prob_home: 0.52,
                        prob_draw: 0.28,
                        prob_away: 0.20,
                        percentiles: { p5: 0.32, p25: 0.45, p50: 0.52, p75: 0.59, p95: 0.68 },
                        notes: 'High volatility environment simulation'
                    },
                    {
                        scenario_type: 'base',
                        parameters: { "variance_multiplier": 1.0 },
                        prob_home: 0.56,
                        prob_draw: 0.25,
                        prob_away: 0.19,
                        percentiles: { p5: 0.38, p25: 0.49, p50: 0.56, p75: 0.64, p95: 0.74 },
                        notes: 'Standard model using secondary feature distribution'
                    },
                    {
                        scenario_type: 'aggressive',
                        parameters: { "variance_multiplier": 0.8 },
                        prob_home: 0.61,
                        prob_draw: 0.22,
                        prob_away: 0.17,
                        percentiles: { p5: 0.45, p25: 0.54, p50: 0.61, p75: 0.68, p95: 0.78 },
                        notes: 'Low volatility, high feature confidence scenario'
                    }
                ],
                uncertainty: {
                    volatility_score: 42.5,
                    data_quality_index: 88.0,
                    confidence_decay: 0.12,
                    factors: {
                        distribution_cv: 0.18,
                        data_age_days: 0.5,
                        feature_coverage: 0.92,
                        sample_size: 1000,
                        event_horizon_days: 2.0
                    },
                    notes: 'Strong overall data coverage with moderate recent volatility'
                }
            },
            uncertainty: {
                volatility_score: 42.5,
                data_quality_index: 88.0,
                confidence_decay: 0.12,
                factors: {
                    distribution_cv: 0.18,
                    data_age_days: 0.5,
                    feature_coverage: 0.92,
                    sample_size: 1000,
                    event_horizon_days: 2.0
                },
                notes: 'Strong overall data coverage with moderate recent volatility'
            },
            cost_tokens: 2,
            transaction_id: `tx_${Math.random().toString(36).substr(2, 9)}`,
            notes: 'Successfully generated with V2 engine'
        };
    }
}

export const api = new TricksterAPI();
