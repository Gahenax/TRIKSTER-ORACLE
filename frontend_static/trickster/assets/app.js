/**
 * TRICKSTER ORACLE — ANALYTICS ENGINE RUNTIME
 * V2 COMPLIANT (Static Module)
 *
 * Contract: POST /api/v2/simulate
 * Headers:  Content-Type, X-User-ID, X-Idempotency-Key
 * Payload:  { sport, primary, opponent, mode }
 */

// ── Helper Functions ──

function getCurrentUserId() {
    const k = 'TRICKSTER_USER_ID';
    let v = localStorage.getItem(k);
    if (!v) {
        v = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));
        localStorage.setItem(k, v);
    }
    return v;
}

function uuidv4() {
    return (crypto.randomUUID
        ? crypto.randomUUID()
        : (Date.now().toString(16) + Math.random().toString(16).slice(2)));
}

// ── Syntax Highlighting ──

function syntaxHighlight(json) {
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 2);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
        function (match) {
            let cls = 'json-num';
            if (/^"/.test(match)) {
                cls = /:$/.test(match) ? 'json-key' : 'json-string';
            } else if (/true|false/.test(match)) {
                cls = 'json-bool';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        }
    );
}

// ── Terminal Renderers ──

function renderTerminalError(tag, message, details) {
    const el = document.getElementById('json-output');
    if (!el) return;
    let html = `<div class="error-block"><strong>${tag}:</strong><br>${message}`;
    if (details) html += `<br><small style="opacity:.7">${details}</small>`;
    html += '</div>';
    el.innerHTML = html;
}

function renderTerminalSuccess(data) {
    const el = document.getElementById('json-output');
    if (!el) return;
    el.innerHTML = `<pre>${syntaxHighlight(data)}</pre>`;
}

// ── Main Application ──

document.addEventListener('DOMContentLoaded', () => {
    const CONFIG = window.TRICKSTER_CONFIG;
    const elements = {
        indicator: document.getElementById('engine-dot'),
        statusText: document.getElementById('engine-status-text'),
        form: document.getElementById('simulation-form'),
        runBtn: document.getElementById('run-simulation'),
        output: document.getElementById('json-output'),
        sport: document.getElementById('sport'),
        actorA: document.getElementById('actorA'),
        actorB: document.getElementById('actorB'),
        mode: document.getElementById('mode'),
        iterations: document.getElementById('iterations')
    };

    /**
     * Initialize Health Check
     */
    async function initConnection() {
        try {
            const response = await fetch(`${CONFIG.API_URL}/ready`);
            const data = await response.json();

            if (data.ready) {
                elements.indicator.className = 'dot active';
                elements.statusText.innerText = 'Engine V2.1 Operational';
            } else {
                elements.indicator.className = 'dot error';
                elements.statusText.innerText = 'Engine Booting/Maintenance';
            }
        } catch (error) {
            elements.indicator.className = 'dot error';
            elements.statusText.innerText = 'Connection Error / CORS';
        }
    }

    /**
     * Execution Handler — V2 Contract
     */
    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // ── Read actor-name inputs ──
        const sport = elements.sport?.value || 'FOOTBALL';
        const primary = elements.actorA?.value?.trim();
        const opponent = elements.actorB?.value?.trim();
        const mode = elements.mode?.value || 'FAST';

        if (!primary || !opponent) {
            renderTerminalError('INPUT_ERROR', 'Ingresa Actor A y Actor B.');
            return;
        }

        const iterationsEl = elements.iterations;
        const iterations = iterationsEl ? Number(iterationsEl.value) : NaN;

        // ── Build v2 payload ──
        const payload = { sport, primary, opponent, mode };
        if (Number.isFinite(iterations)) payload.iterations = iterations;

        // ── UI state: loading ──
        elements.runBtn.disabled = true;
        elements.output.innerHTML = `<div class="placeholder-text">CALCULANDO ESCENARIOS PROBABILÍSTICOS...</div>`;

        try {
            const response = await fetch(`${CONFIG.API_URL}/api/v2/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-User-ID': getCurrentUserId(),
                    'X-Idempotency-Key': uuidv4()
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                // ── Contextual error display ──
                let hint = '';
                if (response.status === 404) {
                    hint = `Endpoint: ${CONFIG.API_URL}/api/v2/simulate — route mismatch. Verify backend routes.`;
                } else if (response.status === 401 || response.status === 403) {
                    hint = 'Missing or invalid X-User-ID header.';
                } else if (response.status === 422) {
                    hint = 'Payload validation failed. Check the request body contract.';
                } else if (response.status >= 500) {
                    const reqId = result.request_id || 'N/A';
                    hint = `Server error (request_id: ${reqId}). Check backend logs.`;
                }

                renderTerminalError(
                    `API_ERROR [${response.status}]`,
                    syntaxHighlight(result),
                    hint
                );
                return;
            }

            // ── Success Display ──
            renderTerminalSuccess(result);

        } catch (err) {
            renderTerminalError('NETWORK_OR_REACHABILITY_ERROR', err.message);
        } finally {
            elements.runBtn.disabled = false;
        }
    });

    initConnection();
});
