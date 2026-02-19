/**
 * DNS-safe API Client with Primary → Fallback failover
 *
 * In development mode (VITE_API_URL set), uses the Vite proxy directly.
 * In production builds, tries the custom domain first, then falls back
 * to the Render.com URL if the primary is unreachable or returns 5xx.
 */

const PRIMARY_API = 'https://trickster-api.gahenaxaisolutions.com';
const FALLBACK_API = 'https://trickster-oracle-api.onrender.com';

const DEV_API_URL = import.meta.env.VITE_API_URL || '';

/**
 * Determines the base URL for API requests.
 * In dev mode, returns the VITE_API_URL (handled by Vite proxy).
 * In production, returns empty string (apiFetch handles routing).
 */
export function getBaseUrl(): string {
    return DEV_API_URL;
}

/**
 * Fetch wrapper with automatic domain failover.
 *
 * @param path - API path (e.g. "/api/v2/simulate")
 * @param options - Standard RequestInit options
 * @returns Response from either primary or fallback API
 *
 * Failover triggers on:
 * - Network errors (DNS failure, timeout, connection refused)
 * - HTTP 5xx responses from primary
 *
 * 4xx responses are returned as-is (not retried).
 */
export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
    // In development mode, use Vite proxy directly (no fallback needed)
    if (DEV_API_URL) {
        return fetch(DEV_API_URL + path, options);
    }

    // Production: try primary domain first
    try {
        const res = await fetch(PRIMARY_API + path, options);

        // Return 4xx as-is (client errors should not trigger fallback)
        if (res.status < 500) {
            return res;
        }

        // 5xx: fall through to fallback
        console.warn(`[Trickster] Primary API returned ${res.status}, switching to fallback`);
    } catch (err) {
        console.warn('[Trickster] Primary API unreachable, using fallback:', (err as Error).message);
    }

    // Fallback
    return fetch(FALLBACK_API + path, options);
}
