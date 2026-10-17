/**
 * Scenario Simulation Component
 */
const ScenarioSimulation = {
    _scenarios: null,

    init() {
        State.subscribe((event, data) => {
            if (event === 'patientLoaded') {
                this.render();
            }
        });

        // Re-render chart on window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (this._scenarios && State.activeTab === 'progression') {
                    const canvas = document.getElementById('canvas-scenario-trajectory');
                    ChartRenderer.renderScenariosPlot(canvas, this._scenarios);
                }
            }, 120);
        });
    },

    render() {
        const full = State.currentPatientFull;
        if (!full) return;

        const scenarios = full.treatment_scenarios;
        const listContainer = document.getElementById('scenarios-list-box');
        if (!listContainer || !scenarios) return;

        this._scenarios = scenarios;

        listContainer.innerHTML = scenarios.map(scen => `
            <div class="scenario-card ${scen.is_active ? 'active' : ''}" data-id="${scen.scenario_id}">
                <div class="scenario-card-header">
                    <span class="scenario-title">${scen.name}</span>
                    <span class="badge ${scen.is_active ? 'badge-success' : 'badge-mono'}">
                        ${scen.is_active ? 'Active Pathway' : 'Hypothetical Pathway'}
                    </span>
                </div>
                <p class="scenario-desc">${scen.description}</p>
                <div class="scenario-card-footer">
                    <span class="badge badge-mono">Type: ${scen.intervention_type}</span>
                    <button class="btn btn-sm ${scen.is_active ? 'btn-secondary' : 'btn-outline-cyan'} btn-activate-scen" data-id="${scen.scenario_id}">
                        ${scen.is_active ? 'Currently Applied' : 'Simulate This Pathway'}
                    </button>
                </div>
            </div>
        `).join('');

        // Bind activation buttons
        listContainer.querySelectorAll('.btn-activate-scen').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const scenId = btn.getAttribute('data-id');
                try {
                    const res = await API.applyTreatment(State.currentPatientId, scenId);
                    App.showToast(`Applied: ${res.active_treatment}`);
                    await State.refreshPatient();
                } catch (err) {
                    App.showToast(`Failed: ${err.message}`);
                }
            });
        });

        // Draw Scenario Trajectory Plot
        const canvas = document.getElementById('canvas-scenario-trajectory');
        ChartRenderer.renderScenariosPlot(canvas, scenarios);

        // Render Legend
        const legendBox = document.getElementById('scenario-trajectory-legend');
        const colors = ['#334155', '#ef4444', '#f59e0b', '#9d4edd'];
        legendBox.innerHTML = scenarios.map((s, idx) => `
            <div class="trajectory-legend-item">
                <span style="width:12px; height:12px; background:${colors[idx % colors.length]}; border-radius:2px; flex-shrink:0;"></span>
                <span>${s.name} ${s.is_active ? '<strong>(Active)</strong>' : ''}</span>
            </div>
        `).join('');
    }
};
