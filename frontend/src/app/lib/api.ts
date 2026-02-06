/**
 * API Client for Trickster Oracle Backend
 * Handles all HTTP communication with the FastAPI backend
 */

import type {
    EventInput,
    SimulationConfig,
    SimulationResult,
    HealthResponse,
    VersionResponse,
    ErrorResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class TricksterAPI {
    async checkHealth(): Promise<HealthResponse> {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error('Backend health check failed');
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
}

export const api = new TricksterAPI();
