document.addEventListener('DOMContentLoaded', () => {
    const config = window.TRICKSTER_CONFIG;
    const indicator = document.getElementById('api-indicator');
    const output = document.getElementById('response-output');
    const form = document.getElementById('demo-form');
    const runBtn = document.getElementById('run-btn');

    // 1. Check API Health
    async function checkHealth() {
        try {
            const resp = await fetch(`${config.API_URL}/ready`);
            const data = await resp.json();
            if (data.ready) {
                indicator.classList.add('online');
                console.log("TRICKSTER: Core systems ready.");
            } else {
                indicator.classList.add('offline');
            }
        } catch (e) {
            indicator.classList.add('offline');
            console.error("TRICKSTER: Connection failed.", e);
        }
    }

    // 2. Handle Simulation
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const simulations = parseInt(document.getElementById('sim-count').value);
        const pA = parseFloat(document.getElementById('prob-a').value);
        const pB = parseFloat(document.getElementById('prob-b').value);

        output.innerHTML = '<span class="status-msg">Procesando simulación Monte Carlo...</span>';
        runBtn.disabled = true;

        try {
            const resp = await fetch(`${config.API_URL}/api/v2/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulations,
                    pA,
                    pB,
                    user_id: "anonymous_demo"
                })
            });

            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(JSON.stringify(errData, null, 2));
            }

            const result = await resp.json();
            output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        } catch (err) {
            output.innerHTML = `<div class="error-text"><strong>ERROR:</strong><br>${err.message}</div>`;
        } finally {
            runBtn.disabled = false;
        }
    });

    checkHealth();
});
