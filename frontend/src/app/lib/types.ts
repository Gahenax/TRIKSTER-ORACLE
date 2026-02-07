/**
 * Type definitions for Trickster Oracle Frontend
 * V2 Specification
 */

export interface EventInput {
    sport: string;
    event_id: string;
    home_team: string;
    away_team: string;
    home_rating: number;
    away_rating: number;
    home_advantage: number;
}

export interface SimulationConfig {
    n_simulations: number;
    ci_level: number;
    seed?: number;
}

// V2 Core Types
export interface ScenarioV2 {
    scenario_type: string;
    parameters: Record<string, number>;
    prob_home: number;
    prob_draw: number;
    prob_away: number;
    percentiles: Record<string, number>;
    notes: string;
}

export interface UncertaintyMetrics {
    volatility_score: number;
    data_quality_index: number;
    confidence_decay: number;
    factors: {
        distribution_cv: number;
        data_age_days: number;
        feature_coverage: number;
        sample_size: number;
        event_horizon_days: number;
    };
    notes: string;
}

export interface DistributionObjectV2 {
    sport: string;
    event_id: string;
    market: string;
    model_version: string;
    n_sims: number;
    ci_level: number;
    seed?: number;
    percentiles: {
        p5: number;
        p25: number;
        p50: number;
        p75: number;
        p95: number;
    };
    mean: number;
    stdev: number;
    skew: number;
    kurtosis: number;
    scenarios: ScenarioV2[];
    uncertainty: UncertaintyMetrics;
}

export interface UserStatus {
    user_id: string;
    daily_used: number;
    daily_limit: number;
    cooldown_until: string | null;
    token_balance: number;
    is_premium: boolean;
    last_reset: string;
}

// Result Wrapper for UI
export interface SimulationResultV2 {
    distribution: DistributionObjectV2;
    uncertainty: UncertaintyMetrics;
    cost_tokens: number;
    transaction_id: string;
    user_status: UserStatus;
    notes: string;
}

// V1 Legacy Support (Internal fallback)
export interface SimulationResult {
    event: EventInput;
    config: SimulationConfig;
    prob_home: number;
    prob_draw?: number;
    prob_away: number;
    distribution: {
        bins: number[];
        frequencies: number[];
    };
    confidence_intervals: Record<string, { lower: number; upper: number }>;
    risk: {
        score: number;
        band: 'LOW' | 'MEDIUM' | 'HIGH';
        rationale: string;
    };
    explanation: {
        summary: string;
        scenarios: Array<{ name: string; probability: number; description: string }>;
        caveats: string[];
        sensitivity: Array<{ factor_name: string; delta_probability: number; impact_level: string }>;
    };
    model_version: string;
    execution_time_ms: number;
    cache_hit: boolean;
}

export interface HealthResponse {
    status: string;
    version: string;
    timestamp: string;
    components: Record<string, string>;
}

export interface VersionResponse {
    version: string;
}

export interface ErrorResponse {
    error_code: string;
    message: string;
    path?: string;
    request_id?: string;
    timestamp: string;
}
