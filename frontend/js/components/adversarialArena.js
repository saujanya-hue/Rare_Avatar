/**
 * Diagnostic AI Adversarial Arena Dashboard Component
 *
 * Implements automated scenario generation, constraint-aware stress-testing,
 * live KPI tracking, comparative failure analysis, deep case diff inspection,
 * history management, and multi-format exports.
 */
const AdversarialArena = {
    currentExperiment: null,
    capabilities: null,
    activeSubtab: 'suite', // 'suite', 'sandbox', 'history'
    activeInspectorTab: 'diff', // 'diff', 'transformations', 'decision', 'constraints', 'evidence'
    selectedCase: null,
    filterDisease: 'all',
    filterFailure: 'all',
    searchQuery: '',

    async init() {
        this.bindEvents();
        try {
            this.capabilities = await API.getArenaCapabilities();
            this.renderCapabilitiesInfo();
        } catch (e) {
            console.warn('Could not fetch arena capabilities:', e);
        }
        await this.loadHistory();
    },

    bindEvents() {
        // Sub-tabs navigation (Suite vs Sandbox vs History)
        document.querySelectorAll('.arena-subtab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.arena-subtab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeSubtab = btn.getAttribute('data-subtab');
                this.updateSubtabVisibility();
            });
        });

        // Quick Random Seed generator
        document.getElementById('btn-arena-random-seed')?.addEventListener('click', () => {
            const seed = Math.floor(10000 + Math.random() * 90000);
            const input = document.getElementById('input-arena-seed');
            if (input) input.value = seed;
            App.showToast(`Randomized seed: ${seed}`);
        });

        // Model selector change (toggle external URL input)
        document.getElementById('select-arena-model')?.addEventListener('change', (e) => {
            const externalBox = document.getElementById('box-arena-external-url');
            if (externalBox) {
                externalBox.classList.toggle('hidden', e.target.value !== 'external_http');
            }
        });

        // Sliders value updates
        const noiseSlider = document.getElementById('input-arena-noise');
        noiseSlider?.addEventListener('input', (e) => {
            const lbl = document.getElementById('label-arena-noise-val');
            if (lbl) lbl.textContent = parseFloat(e.target.value).toFixed(2);
        });

        const missingSlider = document.getElementById('input-arena-missing');
        missingSlider?.addEventListener('input', (e) => {
            const lbl = document.getElementById('label-arena-missing-val');
            if (lbl) lbl.textContent = `${Math.round(parseFloat(e.target.value) * 100)}%`;
        });

        const ageShiftSlider = document.getElementById('input-arena-age-shift');
        ageShiftSlider?.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            const lbl = document.getElementById('label-arena-age-val');
            if (lbl) lbl.textContent = `${val >= 0 ? '+' : ''}${val} yrs`;
        });

        // Launch Experiment button
        document.getElementById('btn-run-arena')?.addEventListener('click', () => {
            this.handleRunExperiment();
        });

        // Filtering cases table
        document.getElementById('filter-arena-disease')?.addEventListener('change', (e) => {
            this.filterDisease = e.target.value;
            this.renderCasesTable();
        });

        document.getElementById('filter-arena-failure')?.addEventListener('change', (e) => {
            this.filterFailure = e.target.value;
            this.renderCasesTable();
        });

        document.getElementById('input-arena-search')?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase().trim();
            this.renderCasesTable();
        });

        // Case Inspector Modal Tabs
        document.querySelectorAll('.inspector-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.inspector-tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeInspectorTab = btn.getAttribute('data-tab');
                this.renderInspectorTabContent();
            });
        });

        // Case Inspector Modal Close
        const inspectorOverlay = document.getElementById('modal-case-inspector');
        document.getElementById('btn-close-inspector')?.addEventListener('click', () => {
            this.closeCaseInspector();
        });

        document.getElementById('btn-close-inspector-footer')?.addEventListener('click', () => {
            this.closeCaseInspector();
        });

        inspectorOverlay?.addEventListener('click', (e) => {
            if (e.target === inspectorOverlay) {
                this.closeCaseInspector();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && inspectorOverlay && !inspectorOverlay.classList.contains('hidden')) {
                this.closeCaseInspector();
            }
        });

        // Export Buttons
        document.getElementById('btn-arena-export-json')?.addEventListener('click', () => {
            this.handleExport('json');
        });

        document.getElementById('btn-arena-export-csv')?.addEventListener('click', () => {
            this.handleExport('csv');
        });

        document.getElementById('btn-arena-copy-config')?.addEventListener('click', () => {
            this.handleCopyConfig();
        });
        document.getElementById('btn-run-breaking-point')?.addEventListener('click', () => {
            this.handleRunBreakingPoint();
        });

        document.getElementById('btn-compare-breaking-point')?.addEventListener('click', () => {
            this.handleCompareBreakingPoint();
        });
    },

    updateSubtabVisibility() {
        document.getElementById('panel-arena-suite')?.classList.toggle('hidden', this.activeSubtab !== 'suite');
        document.getElementById('panel-arena-sandbox')?.classList.toggle('hidden', this.activeSubtab !== 'sandbox');
        document.getElementById('panel-arena-history')?.classList.toggle('hidden', this.activeSubtab !== 'history');
        document.getElementById('panel-arena-breaking-point')?.classList.toggle('hidden', this.activeSubtab !== 'breaking-point');

        if (this.activeSubtab === 'history') {
            this.loadHistory();
        }
    },

    renderCapabilitiesInfo() {
        if (!this.capabilities) return;
        const banner = document.getElementById('arena-capabilities-summary');
        if (banner) {
            banner.textContent = `Supported rare-disease pathophysiological models: Wilson Disease, Fabry Disease, Gaucher Disease Type 1. Automated constraint validation active.`;
        }
    },

    async handleRunExperiment() {
        const diseaseSel = document.getElementById('select-arena-disease')?.value || 'all';
        const modelType = document.getElementById('select-arena-model')?.value || 'reference_baseline';
        const strategy = document.getElementById('select-arena-strategy')?.value || 'sweep';
        const numCases = parseInt(document.getElementById('input-arena-cases')?.value || '4');
        const seed = parseInt(document.getElementById('input-arena-seed')?.value || '42');
        const noise = parseFloat(document.getElementById('input-arena-noise')?.value || '0.15');
        const missing = parseFloat(document.getElementById('input-arena-missing')?.value || '0.25');
        const ageShift = parseInt(document.getElementById('input-arena-age-shift')?.value || '0');
        const infection = document.getElementById('check-arena-infection')?.checked || false;
        const externalUrl = document.getElementById('input-arena-external-url')?.value?.trim() || null;

        if (modelType === 'external_http' && !externalUrl) {
            App.showToast('Please specify a valid external model HTTP endpoint URL.');
            return;
        }

        const config = {
            disease_selection: diseaseSel,
            num_cases_per_disease: numCases,
            random_seed: seed,
            model_type: modelType,
            external_endpoint_url: externalUrl,
            search_strategy: strategy,
            noise_sigma: noise,
            missing_lab_rate: missing,
            atypical_age_shift_years: ageShift,
            inject_confounding_infection: infection,
            max_cases: 50
        };

        const btnRun = document.getElementById('btn-run-arena');
        const spinner = document.getElementById('arena-spinner');

        try {
            if (btnRun) {
                btnRun.disabled = true;
                btnRun.innerHTML = '<span>⚡</span> Running Adversarial Evaluation...';
            }
            if (spinner) spinner.classList.remove('hidden');

            const result = await API.runArenaExperiment(config);
            this.currentExperiment = result;

            this.renderExperimentResults();
            App.showToast(`Adversarial Arena: evaluated ${result.cases.length} cases. Discovered ${result.metrics.failure_count} failure modes.`);
            await this.loadHistory();
        } catch (e) {
            App.showToast(`Adversarial Arena Error: ${e.message}`);
        } finally {
            if (btnRun) {
                btnRun.disabled = false;
                btnRun.innerHTML = '<span>⚡</span> Launch Adversarial Arena Experiment';
            }
            if (spinner) spinner.classList.add('hidden');
        }
    },

    renderExperimentResults() {
        if (!this.currentExperiment) return;
        const exp = this.currentExperiment;
        const m = exp.metrics;

        // 1. Experiment Status Bar
        const badgeId = document.getElementById('arena-exp-id-badge');
        if (badgeId) badgeId.textContent = exp.experiment_id;

        const badgeModel = document.getElementById('arena-exp-model-badge');
        if (badgeModel) badgeModel.textContent = exp.config.model_type.replace('_', ' ').toUpperCase();

        const badgeTime = document.getElementById('arena-exp-time-badge');
        if (badgeTime) badgeTime.textContent = new Date(exp.created_at).toLocaleTimeString();

        // 2. KPI Cards
        const dispBaseAcc = document.getElementById('kpi-baseline-acc');
        if (dispBaseAcc) {
            dispBaseAcc.textContent = m.baseline_accuracy !== null ? `${(m.baseline_accuracy * 100).toFixed(1)}%` : 'N/A';
        }

        const dispPertAcc = document.getElementById('kpi-perturbed-acc');
        if (dispPertAcc) {
            dispPertAcc.textContent = m.perturbed_accuracy !== null ? `${(m.perturbed_accuracy * 100).toFixed(1)}%` : 'N/A';
        }

        const dispDegradation = document.getElementById('kpi-accuracy-degradation');
        if (dispDegradation) {
            if (m.accuracy_degradation !== null) {
                const deg = m.accuracy_degradation * 100;
                dispDegradation.textContent = `${deg > 0 ? '-' : '+'}${Math.abs(deg).toFixed(1)}%`;
                dispDegradation.className = deg > 15 ? 'kpi-val text-crimson' : (deg > 5 ? 'kpi-val text-amber' : 'kpi-val text-emerald');
            } else {
                dispDegradation.textContent = 'N/A';
            }
        }

        const dispInstability = document.getElementById('kpi-instability-rate');
        if (dispInstability) {
            dispInstability.textContent = m.prediction_instability_rate !== null ? `${(m.prediction_instability_rate * 100).toFixed(1)}%` : '0.0%';
        }

        const dispFailures = document.getElementById('kpi-failures-discovered');
        if (dispFailures) {
            dispFailures.textContent = `${m.failure_count} cases (${m.failure_rate !== null ? (m.failure_rate * 100).toFixed(1) : 0}%)`;
        }

        // Cohort counts
        const chipAttempted = document.getElementById('chip-cases-attempted');
        if (chipAttempted) chipAttempted.textContent = m.total_cases_attempted;
        const chipValid = document.getElementById('chip-cases-valid');
        if (chipValid) chipValid.textContent = m.valid_cases_count;
        const chipRejected = document.getElementById('chip-cases-rejected');
        if (chipRejected) chipRejected.textContent = m.rejected_cases_count;
        const chipUneval = document.getElementById('chip-cases-unevaluable');
        if (chipUneval) chipUneval.textContent = m.unevaluable_cases_count;

        // 3. Failure Breakdown Chips
        const fb = m.failure_breakdown || {};
        document.getElementById('cnt-fail-incorrect')?.replaceChildren(document.createTextNode(fb['INCORRECT_PREDICTION'] || 0));
        document.getElementById('cnt-fail-instability')?.replaceChildren(document.createTextNode(fb['PREDICTION_INSTABILITY'] || 0));
        document.getElementById('cnt-fail-collapse')?.replaceChildren(document.createTextNode(fb['CONFIDENCE_COLLAPSE'] || 0));
        document.getElementById('cnt-fail-constraint')?.replaceChildren(document.createTextNode(fb['CONSTRAINT_VIOLATION'] || 0));
        document.getElementById('cnt-fail-unevaluable')?.replaceChildren(document.createTextNode(fb['UNEVALUABLE'] || 0));

        // 4. Comparative Matrix Tables
        this.renderDiseaseMatrix(m.by_disease);
        this.renderPerturbationMatrix(m.by_perturbation_type);

        // 5. Prioritized Cases Table
        this.renderCasesTable();

        // Reveal the results container
        document.getElementById('arena-results-container')?.classList.remove('hidden');
    },

    renderDiseaseMatrix(byDisease) {
        const tbody = document.getElementById('tbody-disease-matrix');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!byDisease || Object.keys(byDisease).length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No disease breakdown available.</td></tr>';
            return;
        }

        const nameMap = {
            'wilson_disease': 'Wilson Disease (ATP7B)',
            'fabry_disease': 'Fabry Disease (GLA)',
            'gaucher_disease': 'Gaucher Disease Type 1 (GBA1)'
        };

        for (const [dId, s] of Object.entries(byDisease)) {
            const tr = document.createElement('tr');
            const deg = s.accuracy_degradation !== null ? (s.accuracy_degradation * 100).toFixed(1) : '—';
            const degColor = s.accuracy_degradation > 0.15 ? 'text-crimson' : (s.accuracy_degradation > 0 ? 'text-amber' : 'text-emerald');

            tr.innerHTML = `
                <td><strong>${nameMap[dId] || dId}</strong></td>
                <td>${s.total_cases}</td>
                <td>${s.valid_cases}</td>
                <td>${s.baseline_accuracy !== null ? (s.baseline_accuracy * 100).toFixed(1) + '%' : '—'}</td>
                <td>${s.perturbed_accuracy !== null ? (s.perturbed_accuracy * 100).toFixed(1) + '%' : '—'}</td>
                <td class="${degColor}"><strong>${deg !== '—' ? '-' + deg + '%' : '—'}</strong></td>
                <td><span class="badge ${s.failure_count > 0 ? 'badge-danger' : 'badge-success'}">${s.failure_count} failures</span></td>
            `;
            tbody.appendChild(tr);
        }
    },

    renderPerturbationMatrix(byPerturbation) {
        const tbody = document.getElementById('tbody-perturbation-matrix');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!byPerturbation || Object.keys(byPerturbation).length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No perturbation breakdown available.</td></tr>';
            return;
        }

        const labelMap = {
            'MEASUREMENT_NOISE': 'Gaussian Measurement Noise (σ)',
            'MISSING_LAB_DROPOUT': 'Missing Laboratory Observations Dropout',
            'ATYPICAL_AGE_SHIFT': 'Atypical Age-of-Onset Shift Window',
            'CONFOUNDING_INFECTION': 'Acute Intercurrent Infection Confounder (CRP/WBC)',
            'COMBINED': 'Multi-Modal Combined Perturbations'
        };

        for (const [pType, s] of Object.entries(byPerturbation)) {
            if (s.cases_evaluated === 0) continue;
            const tr = document.createElement('tr');
            const acc = s.accuracy !== null ? (s.accuracy * 100).toFixed(1) + '%' : '—';
            const failRate = s.failure_rate !== null ? (s.failure_rate * 100).toFixed(1) + '%' : '—';

            tr.innerHTML = `
                <td><strong>${labelMap[pType] || pType}</strong></td>
                <td>${s.cases_evaluated}</td>
                <td>${s.correct_predictions}</td>
                <td><span class="badge ${s.failures_discovered > 0 ? 'badge-warning' : 'badge-info'}">${s.failures_discovered}</span></td>
                <td>${failRate}</td>
            `;
            tbody.appendChild(tr);
        }
    },

    renderCasesTable() {
        const tbody = document.getElementById('tbody-arena-cases');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!this.currentExperiment || !this.currentExperiment.cases.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No cases in active experiment.</td></tr>';
            return;
        }

        let filtered = this.currentExperiment.cases;

        // Disease filter
        if (this.filterDisease !== 'all') {
            filtered = filtered.filter(c => c.disease_id === this.filterDisease);
        }

        // Failure filter
        if (this.filterFailure === 'failures_only') {
            filtered = filtered.filter(c => c.is_failure);
        } else if (this.filterFailure === 'instability_only') {
            filtered = filtered.filter(c => c.is_instability);
        } else if (this.filterFailure === 'rejected_only') {
            filtered = filtered.filter(c => c.evaluation_status === 'REJECTED');
        }

        // Search query
        if (this.searchQuery) {
            filtered = filtered.filter(c =>
                c.case_id.toLowerCase().includes(this.searchQuery) ||
                c.disease_name.toLowerCase().includes(this.searchQuery) ||
                c.diff_summary.toLowerCase().includes(this.searchQuery) ||
                (c.perturbed_prediction && c.perturbed_prediction.predicted_disease_name.toLowerCase().includes(this.searchQuery))
            );
        }

        if (!filtered.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No cases match the selected filters.</td></tr>';
            return;
        }

        // Prioritize failure cases first
        filtered.sort((a, b) => {
            if (a.is_failure && !b.is_failure) return -1;
            if (!a.is_failure && b.is_failure) return 1;
            return 0;
        });

        filtered.forEach(c => {
            const tr = document.createElement('tr');
            if (c.is_failure) tr.classList.add('row-failure-highlight');

            // Category badge
            let catBadge = '';
            if (c.failure_category === 'INCORRECT_PREDICTION') {
                catBadge = '<span class="badge badge-danger">Incorrect Prediction</span>';
            } else if (c.failure_category === 'PREDICTION_INSTABILITY') {
                catBadge = '<span class="badge badge-warning">Prediction Instability</span>';
            } else if (c.failure_category === 'CONFIDENCE_COLLAPSE') {
                catBadge = '<span class="badge badge-warning">Confidence Collapse</span>';
            } else if (c.failure_category === 'CONSTRAINT_VIOLATION') {
                catBadge = '<span class="badge badge-danger">Constraint Violation</span>';
            } else if (c.failure_category === 'UNEVALUABLE') {
                catBadge = '<span class="badge badge-mono">Unevaluable</span>';
            } else {
                catBadge = '<span class="badge badge-success">Robust Match</span>';
            }

            const basePred = c.baseline_prediction ? c.baseline_prediction.predicted_disease_name : '—';
            const pertPred = c.perturbed_prediction ? c.perturbed_prediction.predicted_disease_name : '—';
            const isMatch = c.perturbed_prediction ? c.perturbed_prediction.is_top1_correct : false;

            tr.innerHTML = `
                <td><span class="badge badge-mono">${c.case_id}</span></td>
                <td><strong>${c.disease_name}</strong></td>
                <td>${basePred}</td>
                <td class="${isMatch ? 'text-emerald' : 'text-crimson'}"><strong>${pertPred}</strong></td>
                <td><span class="badge badge-mono">${c.ground_truth_disease_name}</span></td>
                <td>${catBadge}</td>
                <td><small class="text-muted">${c.diff_summary}</small></td>
                <td>
                    <button class="btn btn-sm btn-outline-cyan btn-inspect-case" data-case-id="${c.case_id}">
                        🔍 Inspect Diff
                    </button>
                </td>
            `;

            tr.querySelector('.btn-inspect-case')?.addEventListener('click', () => {
                this.openCaseInspector(c.case_id);
            });

            tbody.appendChild(tr);
        });
    },

    async openCaseInspector(caseId) {
        try {
            const caseData = await API.getArenaCase(caseId);
            this.selectedCase = caseData;
            this.renderInspectorModal();
            document.getElementById('modal-case-inspector')?.classList.remove('hidden');
        } catch (e) {
            App.showToast(`Failed to load case: ${e.message}`);
        }
    },

    closeCaseInspector() {
        document.getElementById('modal-case-inspector')?.classList.add('hidden');
    },

    renderInspectorModal() {
        if (!this.selectedCase) return;
        const c = this.selectedCase;

        document.getElementById('inspector-case-id-badge').textContent = c.case_id;
        document.getElementById('inspector-disease-title').textContent = `${c.disease_name} (${c.ground_truth_omim})`;
        document.getElementById('inspector-seed-badge').textContent = `Seed: ${c.seed}`;

        const statusBadge = document.getElementById('inspector-status-badge');
        statusBadge.textContent = c.evaluation_status;
        statusBadge.className = `badge ${c.evaluation_status === 'EVALUATED' ? 'badge-success' : 'badge-danger'}`;

        const failBadge = document.getElementById('inspector-failure-badge');
        failBadge.textContent = c.failure_category.replace('_', ' ');
        failBadge.className = `badge ${c.is_failure ? 'badge-danger' : 'badge-info'}`;

        this.renderInspectorTabContent();
    },

    renderInspectorTabContent() {
        if (!this.selectedCase) return;
        const c = this.selectedCase;
        const container = document.getElementById('inspector-tab-content');
        if (!container) return;

        if (this.activeInspectorTab === 'diff') {
            // Side-by-side comparison
            const orig = c.original_inputs || {};
            const pert = c.blinded_inputs || {};

            let labDiffHtml = '';
            const origLabs = orig.laboratory || [];
            const pertLabs = pert.laboratory || [];
            const pertLabMap = new Map(pertLabs.map(l => [l.test_code, l]));

            origLabs.forEach(ol => {
                const pl = pertLabMap.get(ol.test_code);
                if (!pl) {
                    labDiffHtml += `
                        <div class="diff-entry diff-removed">
                            <span class="diff-tag tag-del">WITHHELD</span>
                            <strong>${ol.test_name} (${ol.test_code}):</strong> ${ol.value} ${ol.unit} (Omitted to test missing data)
                        </div>
                    `;
                } else if (Math.abs(pl.value - ol.value) > 0.01) {
                    const delta = (pl.value - ol.value).toFixed(2);
                    labDiffHtml += `
                        <div class="diff-entry diff-modified">
                            <span class="diff-tag tag-mod">NOISE</span>
                            <strong>${ol.test_name} (${ol.test_code}):</strong> ${ol.value} ${ol.unit} ➔ <span class="highlight-cyan">${pl.value} ${pl.unit}</span> (Δ ${delta > 0 ? '+' : ''}${delta})
                        </div>
                    `;
                } else {
                    labDiffHtml += `
                        <div class="diff-entry diff-unchanged">
                            <span class="diff-tag tag-eq">NORMAL</span>
                            ${ol.test_name}: ${ol.value} ${ol.unit}
                        </div>
                    `;
                }
            });

            // Extra confounder labs
            pertLabs.forEach(pl => {
                if (pl.test_code === 'CRP' || pl.test_code === 'WBC') {
                    labDiffHtml += `
                        <div class="diff-entry diff-added">
                            <span class="diff-tag tag-add">CONFOUNDER</span>
                            <strong>${pl.test_name} (${pl.test_code}):</strong> ${pl.value} ${pl.unit} (Acute Inflammatory Confounder Injected)
                        </div>
                    `;
                }
            });

            container.innerHTML = `
                <div class="inspector-diff-grid">
                    <div class="diff-panel glass-card">
                        <h4>Patient Demographics & Shift</h4>
                        <p><strong>Baseline Age:</strong> ${orig.demographics?.age_years || '—'} yrs | <strong>Sex:</strong> ${orig.demographics?.biological_sex || '—'} | <strong>Ethnicity:</strong> ${orig.demographics?.ethnicity || '—'}</p>
                        <p><strong>Perturbed Age:</strong> <span class="highlight-cyan">${pert.demographics?.age_years || '—'} yrs</span></p>
                        <h4 style="margin-top:16px;">Laboratory Workup Differences</h4>
                        <div class="diff-entries-list">${labDiffHtml}</div>
                    </div>
                    <div class="diff-panel glass-card">
                        <h4>Multi-Modal Imaging Signs (Blinded to Algorithm)</h4>
                        <ul class="imaging-findings-list">
                            ${(pert.imaging_summary || []).map(img => `
                                <li><strong>${img.modality} (${img.anatomical_region}):</strong> ${img.findings}
                                <br><small class="text-cyan">Signs: ${(img.pathological_signs || []).join(', ') || 'None noted'}</small></li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } else if (this.activeInspectorTab === 'transformations') {
            const trans = c.applied_transformations || [];
            if (!trans.length) {
                container.innerHTML = '<p class="text-muted text-center" style="padding:20px;">No transformations were applied to this case (clean baseline).</p>';
                return;
            }
            container.innerHTML = `
                <table class="arena-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Target Feature</th>
                            <th>Original Value</th>
                            <th>Perturbed Value</th>
                            <th>Delta</th>
                            <th>Clinical Rationale</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${trans.map(t => `
                            <tr>
                                <td><span class="badge badge-mono">${t.transformation_type}</span></td>
                                <td><strong>${t.feature_name}</strong></td>
                                <td>${t.original_value}</td>
                                <td><span class="highlight-cyan">${t.perturbed_value}</span></td>
                                <td><span class="badge badge-warning">${t.delta || '—'}</span></td>
                                <td><small>${t.reason}</small></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else if (this.activeInspectorTab === 'decision') {
            const b = c.baseline_prediction;
            const p = c.perturbed_prediction;

            container.innerHTML = `
                <div class="decision-comparison-grid">
                    <div class="decision-card glass-card">
                        <h4>Baseline Model Prediction (Unperturbed)</h4>
                        <p><strong>Predicted:</strong> ${b ? b.predicted_disease_name : 'N/A'}</p>
                        <p><strong>Confidence:</strong> ${b ? (b.confidence_score * 100).toFixed(1) + '%' : 'N/A'}</p>
                        <p><strong>Top-1 Correct:</strong> <span class="badge ${b && b.is_top1_correct ? 'badge-success' : 'badge-danger'}">${b ? b.is_top1_correct : false}</span></p>
                        <p><strong>Reasoning:</strong> <small class="text-muted">${b ? b.reasoning : 'None'}</small></p>
                    </div>
                    <div class="decision-card glass-card">
                        <h4>Perturbed Model Prediction (Under Adversarial Stress)</h4>
                        <p><strong>Predicted:</strong> <span class="${p && p.is_top1_correct ? 'text-emerald' : 'text-crimson'}"><strong>${p ? p.predicted_disease_name : 'N/A'}</strong></span></p>
                        <p><strong>Confidence:</strong> ${p ? (p.confidence_score * 100).toFixed(1) + '%' : 'N/A'}</p>
                        <p><strong>Top-1 Correct:</strong> <span class="badge ${p && p.is_top1_correct ? 'badge-success' : 'badge-danger'}">${p ? p.is_top1_correct : false}</span></p>
                        <p><strong>Reasoning:</strong> <small class="text-muted">${p ? p.reasoning : 'None'}</small></p>
                    </div>
                </div>
            `;
        } else if (this.activeInspectorTab === 'constraints') {
            const cv = c.constraint_validation || {};
            const details = cv.details || [];
            container.innerHTML = `
                <div class="constraints-card glass-card" style="padding:16px;">
                    <h4>Pathophysiological Model Constraint Audit</h4>
                    <p>Status: <span class="badge ${cv.is_valid ? 'badge-success' : 'badge-danger'}">${cv.status}</span></p>
                    ${cv.violations && cv.violations.length ? `
                        <div class="alert-box alert-danger" style="margin-top:10px;">
                            <strong>Fatal Constraint Violations (Impossible Patient Combinations):</strong>
                            <ul>${cv.violations.map(v => `<li>${v}</li>`).join('')}</ul>
                        </div>
                    ` : '<p class="text-emerald" style="margin-top:8px;">✔ No fatal physiological constraint violations detected.</p>'}
                    <table class="arena-table" style="margin-top:14px;">
                        <thead>
                            <tr>
                                <th>Constraint Rule</th>
                                <th>Test Code</th>
                                <th>Observed Value</th>
                                <th>Severity</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${details.map(d => `
                                <tr>
                                    <td><strong>${d.rule_name}</strong><br><small class="text-muted">${d.description || ''}</small></td>
                                    <td><code>${d.test_code}</code></td>
                                    <td>${d.observed_value}</td>
                                    <td><span class="badge badge-mono">${d.severity}</span></td>
                                    <td><span class="badge ${d.passed ? 'badge-success' : 'badge-danger'}">${d.passed ? 'PASSED' : 'VIOLATED'}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else if (this.activeInspectorTab === 'evidence') {
            const evList = c.evidence_provenance || [];
            container.innerHTML = `
                <div class="evidence-card glass-card" style="padding:16px;">
                    <h4>Biomedical Literature Grounding & Evidence Provenance</h4>
                    <p class="text-muted">Synthetic avatar attributes, laboratory distributions, and clinical constraints are derived from peer-reviewed evidence:</p>
                    <ul class="evidence-keys-list" style="margin-top:12px;">
                        ${evList.map(k => `
                            <li>
                                <span class="badge badge-mono">${k}</span>
                                <small class="text-muted">Grounding disease pathophysiological bounds and diagnostic criteria.</small>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
    },

    async loadHistory() {
        try {
            const history = await API.listArenaExperiments();
            const tbody = document.getElementById('tbody-arena-history');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (!history.length) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No historical experiments recorded yet.</td></tr>';
                return;
            }

            history.forEach(exp => {
                const tr = document.createElement('tr');
                const deg = exp.accuracy_degradation !== null ? (exp.accuracy_degradation * 100).toFixed(1) : '—';
                const timeStr = new Date(exp.created_at).toLocaleString();

                tr.innerHTML = `
                    <td><span class="badge badge-mono">${exp.experiment_id}</span></td>
                    <td><small>${timeStr}</small></td>
                    <td><strong>${exp.disease_selection}</strong></td>
                    <td>${exp.model_type}</td>
                    <td>${exp.valid_cases}/${exp.total_cases}</td>
                    <td>${exp.perturbed_accuracy !== null ? (exp.perturbed_accuracy * 100).toFixed(1) + '%' : '—'}</td>
                    <td><span class="badge ${exp.failure_count > 0 ? 'badge-danger' : 'badge-success'}">${exp.failure_count} failures</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-cyan btn-reload-exp" data-exp-id="${exp.experiment_id}">
                            Load Results
                        </button>
                    </td>
                `;

                tr.querySelector('.btn-reload-exp')?.addEventListener('click', async () => {
                    await this.loadExperimentById(exp.experiment_id);
                });

                tbody.appendChild(tr);
            });
        } catch (e) {
            console.warn('Could not load arena history:', e);
        }
    },

    async loadExperimentById(experimentId) {
        try {
            const exp = await API.getArenaExperiment(experimentId);
            this.currentExperiment = exp;
            this.activeSubtab = 'suite';
            this.updateSubtabVisibility();
            document.querySelectorAll('.arena-subtab-btn').forEach(b => {
                b.classList.toggle('active', b.getAttribute('data-subtab') === 'suite');
            });
            this.renderExperimentResults();
            App.showToast(`Loaded experiment ${experimentId}`);
        } catch (e) {
            App.showToast(`Failed to load experiment: ${e.message}`);
        }
    },

    handleExport(format) {
        if (!this.currentExperiment) {
            App.showToast('Run an experiment before exporting results.');
            return;
        }
        const expId = this.currentExperiment.experiment_id;
        const url = `/api/diagnostic-arena/experiments/${expId}/export?format=${format}`;
        window.open(url, '_blank');
        App.showToast(`Exported ${format.toUpperCase()} for ${expId}`);
    },

    handleCopyConfig() {
        if (!this.currentExperiment) {
            App.showToast('Run an experiment first to copy its configuration.');
            return;
        }
        const cfg = this.currentExperiment.config;
        const jsonStr = JSON.stringify(cfg, null, 2);
        navigator.clipboard.writeText(jsonStr).then(() => {
            App.showToast('Experiment configuration copied to clipboard.');
        }).catch(() => {
            App.showToast('Could not copy to clipboard.');
        });
    },

    // ========================================================================
    // DIAGNOSTIC AI BREAKING POINT FINDER
    // ========================================================================
    async handleRunBreakingPoint() {
        const disease = document.getElementById('select-bp-disease')?.value || 'wilson_disease';
        const model = document.getElementById('select-bp-model')?.value || 'mock_fragile';
        const param = document.getElementById('select-bp-param')?.value || 'noise_sigma';
        const stepSize = parseFloat(document.getElementById('input-bp-step-size')?.value || '0.05');
        const maxSteps = parseInt(document.getElementById('input-bp-max-steps')?.value || '12');
        const seed = parseInt(document.getElementById('input-bp-seed')?.value || '42');

        const spinner = document.getElementById('bp-spinner');
        if (spinner) spinner.classList.remove('hidden');

        try {
            App.showToast(`Searching for minimal breaking point along ${param}...`);
            const result = await API.searchBreakingPoint({
                disease_id: disease,
                model_type: model,
                search_axis: param,
                step_size: stepSize,
                max_steps: maxSteps,
                random_seed: seed
            });

            this.renderBreakingPointResult(result);
            const deltaStr = result.minimal_delta?.label || (result.minimal_delta?.value !== undefined ? result.minimal_delta.value.toFixed(3) : 'None');
            App.showToast(result.breaking_point_found 
                ? `Breaking point discovered! Minimal delta: ${deltaStr}`
                : 'Model remained robust across all search steps.');
        } catch (e) {
            console.error('Breaking point search failed:', e);
            App.showToast(`Search error: ${e.message}`);
        } finally {
            if (spinner) spinner.classList.add('hidden');
        }
    },

    renderBreakingPointResult(res) {
        const container = document.getElementById('bp-results-container');
        if (!container) return;
        container.classList.remove('hidden');
        document.getElementById('bp-comparison-card')?.classList.add('hidden');

        // Status banner
        const statusBadge = document.getElementById('bp-status-badge');
        if (statusBadge) {
            statusBadge.textContent = res.breaking_point_found ? 'BREAKING POINT IDENTIFIED' : 'ROBUST (NO COLLAPSE)';
            statusBadge.className = res.breaking_point_found ? 'badge badge-danger' : 'badge badge-success';
        }

        const deltaEl = document.getElementById('bp-minimal-delta');
        if (deltaEl) {
            deltaEl.textContent = res.minimal_delta?.label || (res.minimal_delta?.value !== undefined ? res.minimal_delta.value.toFixed(3) : 'None');
        }

        const modeEl = document.getElementById('bp-failure-mode');
        if (modeEl) modeEl.textContent = res.failure_type || 'None';

        const stepsEl = document.getElementById('bp-steps-count');
        if (stepsEl) stepsEl.textContent = `${res.steps_evaluated} Steps`;

        const baseAccEl = document.getElementById('bp-baseline-confidence');
        if (baseAccEl) {
            const conf = res.baseline_prediction?.confidence_score ?? 0;
            baseAccEl.textContent = `${(conf * 100).toFixed(1)}%`;
        }

        const finalAccEl = document.getElementById('bp-broken-confidence');
        if (finalAccEl) {
            const conf = res.breaking_prediction?.confidence_score ?? 0;
            finalAccEl.textContent = `${(conf * 100).toFixed(1)}%`;
        }

        // Progressive Steps Table
        const tbody = document.getElementById('tbody-bp-steps');
        if (tbody && res.step_history) {
            tbody.innerHTML = res.step_history.map(step => {
                const isBreak = step.is_breaking_point;
                const rowClass = isBreak ? 'style="background: rgba(239, 68, 68, 0.08); font-weight: 600;"' : '';
                return `
                    <tr ${rowClass}>
                        <td><strong>Step ${step.step_index}</strong> ${isBreak ? '<span class="badge badge-danger">BREAK</span>' : ''}</td>
                        <td style="font-family:var(--font-mono);">${step.parameter_value.toFixed(3)} (${step.parameter_label})</td>
                        <td>${step.predicted_disease_name}</td>
                        <td style="font-family:var(--font-mono);">${(step.confidence_score * 100).toFixed(1)}%</td>
                        <td><span class="badge ${step.is_top1_correct ? 'badge-success' : 'badge-danger'}">${step.is_top1_correct ? 'CORRECT' : 'INCORRECT'}</span></td>
                        <td><span class="badge ${step.is_clinically_valid ? 'badge-success' : 'badge-warning'}">${step.validation_status}</span></td>
                        <td>${step.failure_mode || 'STABLE'}</td>
                    </tr>
                `;
            }).join('');
        }
    },

    async handleCompareBreakingPoint() {
        const disease = document.getElementById('select-bp-disease')?.value || 'wilson_disease';
        const param = document.getElementById('select-bp-param')?.value || 'noise_sigma';
        const stepSize = parseFloat(document.getElementById('input-bp-step-size')?.value || '0.05');
        const maxSteps = parseInt(document.getElementById('input-bp-max-steps')?.value || '12');
        const seed = parseInt(document.getElementById('input-bp-seed')?.value || '42');

        const spinner = document.getElementById('bp-spinner');
        if (spinner) spinner.classList.remove('hidden');

        try {
            App.showToast(`Benchmarking all diagnostic models for breaking points...`);
            const report = await API.compareBreakingPoint({
                disease_id: disease,
                search_axis: param,
                models: ['reference_baseline', 'mock_fragile', 'mock_robust'],
                step_size: stepSize,
                max_steps: maxSteps,
                random_seed: seed
            });

            this.renderBreakingPointComparison(report);
            App.showToast('Model breaking point comparison completed!');
        } catch (e) {
            console.error('Comparison error:', e);
            App.showToast(`Comparison error: ${e.message}`);
        } finally {
            if (spinner) spinner.classList.add('hidden');
        }
    },

    renderBreakingPointComparison(report) {
        const container = document.getElementById('bp-results-container');
        if (container) container.classList.remove('hidden');

        const compCard = document.getElementById('bp-comparison-card');
        if (!compCard) return;
        compCard.classList.remove('hidden');

        const tbody = document.getElementById('tbody-bp-comparison');
        if (tbody && report.results) {
            tbody.innerHTML = Object.entries(report.results).map(([modelName, res]) => {
                const deltaStr = res.minimal_delta?.label || (res.minimal_delta?.value !== undefined ? res.minimal_delta.value.toFixed(3) : 'Never Collapsed');
                const baseConf = res.baseline_prediction?.confidence_score ?? 0;
                const breakConf = res.breaking_prediction?.confidence_score ?? 0;
                return `
                    <tr>
                        <td><strong>${modelName}</strong></td>
                        <td>
                            <span class="badge ${res.breaking_point_found ? 'badge-danger' : 'badge-success'}">
                                ${res.breaking_point_found ? 'VULNERABLE' : 'ROBUST'}
                            </span>
                        </td>
                        <td style="font-family:var(--font-mono); font-weight:700; color:var(--accent-cyan);">
                            ${deltaStr}
                        </td>
                        <td>${res.failure_type || 'None'}</td>
                        <td>Step ${res.steps_evaluated}</td>
                        <td>${(baseConf * 100).toFixed(1)}% &rarr; ${(breakConf * 100).toFixed(1)}%</td>
                    </tr>
                `;
            }).join('');
        }
    }
};
