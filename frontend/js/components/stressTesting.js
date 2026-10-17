/**
 * Diagnostic Algorithm Stress-Testing Component
 */
const StressTesting = {
    currentTestCase: null,
    currentInspectTab: 'blinded',

    init() {
        // Slider value labels
        const noiseInput = document.getElementById('input-noise-sigma');
        noiseInput?.addEventListener('input', (e) => {
            document.getElementById('label-noise-val').textContent = parseFloat(e.target.value).toFixed(2);
        });

        const missingInput = document.getElementById('input-missing-rate');
        missingInput?.addEventListener('input', (e) => {
            document.getElementById('label-missing-val').textContent = `${Math.round(parseFloat(e.target.value) * 100)}%`;
        });

        const ageShiftInput = document.getElementById('input-age-shift');
        ageShiftInput?.addEventListener('input', (e) => {
            const v = parseInt(e.target.value);
            document.getElementById('label-age-shift-val').textContent = `${v >= 0 ? '+' : ''}${v} yrs`;
        });

        // Generate test case button
        document.getElementById('btn-create-test-case')?.addEventListener('click', () => {
            this.handleCreateTestCase();
        });

        // Test case inspect tabs
        document.querySelectorAll('.tc-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tc-tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentInspectTab = btn.getAttribute('data-view');
                this.renderTestCaseJSON();
            });
        });

        // Evaluate reference model button
        document.getElementById('btn-eval-reference-model')?.addEventListener('click', () => {
            this.handleEvaluateBaseline();
        });

        this.loadHistory();
    },

    async handleCreateTestCase() {
        if (!State.currentPatientId) {
            App.showToast('Select an active patient avatar first.');
            return;
        }

        const noise = parseFloat(document.getElementById('input-noise-sigma').value);
        const missing = parseFloat(document.getElementById('input-missing-rate').value);
        const ageShift = parseInt(document.getElementById('input-age-shift').value);
        const infection = document.getElementById('check-inject-infection').checked;
        const seed = parseInt(document.getElementById('input-perturbation-seed').value) || 42;

        try {
            const tc = await API.createTestCase(State.currentPatientId, noise, missing, ageShift, infection, seed);
            this.currentTestCase = tc;
            document.getElementById('active-test-case-badge').textContent = tc.test_case_id;
            document.getElementById('btn-eval-reference-model').disabled = false;
            this.renderTestCaseJSON();
            App.showToast(`Synthesized test case: ${tc.test_case_id}`);
        } catch (e) {
            App.showToast(`Failed: ${e.message}`);
        }
    },

    renderTestCaseJSON() {
        const viewer = document.getElementById('json-testcase-viewer');
        if (!this.currentTestCase) {
            viewer.textContent = '// Generate a perturbed test case to inspect inputs';
            return;
        }

        if (this.currentInspectTab === 'blinded') {
            const blindedView = {
                test_case_id: this.currentTestCase.test_case_id,
                demographics: this.currentTestCase.input_demographics,
                symptoms_reported: this.currentTestCase.input_symptoms,
                laboratory_tests: this.currentTestCase.input_laboratory,
                imaging_findings: this.currentTestCase.input_imaging_summary
            };
            viewer.textContent = JSON.stringify(blindedView, null, 2);
        } else {
            const groundTruthView = {
                test_case_id: this.currentTestCase.test_case_id,
                ground_truth_disease_id: this.currentTestCase.ground_truth_disease_id,
                ground_truth_disease_name: this.currentTestCase.ground_truth_disease_name,
                ground_truth_omim: this.currentTestCase.ground_truth_omim,
                ground_truth_stage: this.currentTestCase.ground_truth_stage,
                perturbation_applied: this.currentTestCase.perturbation_applied
            };
            viewer.textContent = JSON.stringify(groundTruthView, null, 2);
        }
    },

    async handleEvaluateBaseline() {
        if (!this.currentTestCase) return;

        try {
            const res = await API.evaluateBaseline(this.currentTestCase.test_case_id);
            App.showToast(`Evaluated: ${res.is_top1_correct ? 'Correct Diagnosis!' : 'Diagnostic Error'}`);
            await this.loadHistory();
        } catch (e) {
            App.showToast(`Evaluation failed: ${e.message}`);
        }
    },

    async loadHistory() {
        try {
            const history = await API.getBenchmarkHistory();
            const tbody = document.getElementById('eval-history-tbody');
            if (!tbody) return;

            if (history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No test cases evaluated yet in this session.</td></tr>`;
                return;
            }

            tbody.innerHTML = history.slice().reverse().map(h => `
                <tr>
                    <td style="font-family:var(--font-mono); font-size:0.75rem;"><strong>${h.test_case_id}</strong></td>
                    <td>${h.algorithm_name}</td>
                    <td class="highlight-purple">${h.ground_truth}</td>
                    <td class="${h.is_top1_correct ? 'highlight-cyan' : 'text-danger'}">${h.prediction}</td>
                    <td>${(h.confidence * 100).toFixed(1)}%</td>
                    <td>
                        <span class="badge ${h.is_top1_correct ? 'badge-success' : 'badge-danger'}">
                            ${h.is_top1_correct ? 'TOP-1 HIT' : 'MISS'}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-mono" style="color:var(--accent-cyan);">${(h.robustness_score * 100).toFixed(0)}%</span>
                    </td>
                    <td style="font-size:0.75rem; color:#94a3b8;">${h.perturbation_summary}</td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('Failed to load history:', e);
        }
    }
};
