/**
 * Trainee Diagnostics Component
 * Allows clinical trainees to formulate and submit their primary and differential
 * diagnoses for synthetic patient avatars, obtaining instant scoring and feedback.
 */
const TraineeDiagnostics = {
    submissionsHistory: [],

    init() {
        this.bindEvents();
        State.subscribe((event, data) => {
            if (event === 'patientLoaded') {
                this.updateActivePatientInfo();
            }
        });
    },

    bindEvents() {
        const form = document.getElementById('form-trainee-diagnosis');
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit();
        });

        // Quick fill differential chips
        document.querySelectorAll('.diff-suggest-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const disease = chip.getAttribute('data-disease');
                const primarySelect = document.getElementById('select-trainee-primary-diagnosis');
                if (primarySelect && !primarySelect.value) {
                    primarySelect.value = disease;
                } else {
                    const diffInput = document.getElementById('input-trainee-differentials');
                    if (diffInput) {
                        const current = diffInput.value.trim();
                        diffInput.value = current ? `${current}, ${disease}` : disease;
                    }
                }
            });
        });
    },

    updateActivePatientInfo() {
        const patient = State.currentTraineeView || State.currentPatientFull;
        if (!patient) return;

        const badge = document.getElementById('trainee-eval-patient-id');
        if (badge) badge.textContent = patient.patient_id;

        const countBadge = document.getElementById('trainee-eval-tests-count');
        const testsCount = patient.ordered_tests ? patient.ordered_tests.length : 0;
        if (countBadge) countBadge.textContent = `${testsCount} Tests Ordered`;

        const monthBadge = document.getElementById('trainee-eval-sim-month');
        if (monthBadge) monthBadge.textContent = `Sim Month: ${patient.current_simulation_month}`;
    },

    async handleSubmit() {
        if (!State.currentPatientId) {
            App.showToast('Please select an active patient avatar first.');
            return;
        }

        const user = State.currentUser;
        if (!user) {
            App.showToast('Please sign in as a trainee to submit your diagnosis.');
            return;
        }

        const primarySelect = document.getElementById('select-trainee-primary-diagnosis');
        const diffInput = document.getElementById('input-trainee-differentials');
        const justInput = document.getElementById('textarea-trainee-justification');

        const primaryDiagnosis = primarySelect?.value || '';
        if (!primaryDiagnosis) {
            App.showToast('Please select your Primary Clinical Diagnosis.');
            return;
        }

        const diffText = diffInput?.value || '';
        const differentials = diffText.split(',').map(s => s.trim()).filter(Boolean);
        const justification = justInput?.value || '';

        const patient = State.currentTraineeView || State.currentPatientFull;
        const ordered = patient && patient.ordered_tests ? patient.ordered_tests : [];

        const payload = {
            patient_id: State.currentPatientId,
            trainee_id: user.user_id,
            trainee_email: user.email,
            primary_diagnosis: primaryDiagnosis,
            differential_diagnoses: differentials,
            clinical_justification: justification,
            months_elapsed: patient ? patient.current_simulation_month : 0,
            ordered_investigations: ordered
        };

        const btnSubmit = document.getElementById('btn-submit-trainee-eval');
        try {
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.textContent = 'Evaluating Diagnosis...';
            }

            const result = await API.submitTraineeDiagnosis(payload);
            this.renderEvaluationScorecard(result);
            this.submissionsHistory.unshift(result);
            this.renderHistoryTable();
            App.showToast(`Evaluation completed: Score ${result.accuracy_score}%`);
        } catch (err) {
            console.error('Diagnosis evaluation error:', err);
            App.showToast(err.message || 'Failed to evaluate diagnosis.');
        } finally {
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.textContent = 'Submit Diagnosis for Clinical Scoring';
            }
        }
    },

    renderEvaluationScorecard(result) {
        const scorecardBox = document.getElementById('trainee-scorecard-box');
        if (!scorecardBox) return;

        scorecardBox.classList.remove('hidden');
        scorecardBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        const outcomeBadge = document.getElementById('scorecard-outcome-badge');
        if (outcomeBadge) {
            outcomeBadge.className = result.is_correct ? 'badge badge-success' : 'badge badge-danger';
            outcomeBadge.textContent = result.is_correct ? '✅ CORRECT PRIMARY DIAGNOSIS' : '❌ INCORRECT PRIMARY DIAGNOSIS';
        }

        const accElem = document.getElementById('scorecard-accuracy-val');
        if (accElem) {
            accElem.textContent = `${result.accuracy_score.toFixed(0)}%`;
            accElem.className = result.accuracy_score >= 80 ? 'kpi-val text-emerald' : 'kpi-val text-amber';
        }

        const effElem = document.getElementById('scorecard-efficiency-val');
        if (effElem) {
            effElem.textContent = `${result.efficiency_score.toFixed(0)}%`;
            effElem.className = result.efficiency_score >= 75 ? 'kpi-val text-emerald' : 'kpi-val text-amber';
        }

        const gtElem = document.getElementById('scorecard-ground-truth-name');
        if (gtElem) gtElem.textContent = result.ground_truth_disease_name;

        const debriefElem = document.getElementById('scorecard-debrief-text');
        if (debriefElem) debriefElem.textContent = result.supervisor_debriefing;

        // Detected hallmarks list
        const detectedList = document.getElementById('scorecard-detected-hallmarks');
        if (detectedList) {
            detectedList.innerHTML = result.hallmarks_detected.length > 0
                ? result.hallmarks_detected.map(h => `<li><span class="text-emerald">✓</span> <strong>${h}</strong></li>`).join('')
                : '<li class="text-muted">No specific key hallmarks documented in trainee workup.</li>';
        }

        // Missed hallmarks list
        const missedList = document.getElementById('scorecard-missed-hallmarks');
        if (missedList) {
            missedList.innerHTML = result.missed_hallmarks.length > 0
                ? result.missed_hallmarks.map(h => `<li><span class="text-crimson">⚠</span> <strong>${h}</strong></li>`).join('')
                : '<li class="text-emerald">✓ None! Complete guideline-concordant hallmark investigation achieved.</li>';
        }
    },

    renderHistoryTable() {
        const tbody = document.getElementById('trainee-history-tbody');
        if (!tbody) return;

        if (this.submissionsHistory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center;">No diagnostic submissions yet in this session.</td></tr>';
            return;
        }

        tbody.innerHTML = this.submissionsHistory.map(item => `
            <tr>
                <td><strong>${item.submission_id}</strong></td>
                <td><span class="badge badge-mono">${item.patient_id}</span></td>
                <td>${item.primary_diagnosis}</td>
                <td>${item.ground_truth_disease_name}</td>
                <td>
                    <span class="badge ${item.is_correct ? 'badge-success' : 'badge-danger'}">
                        ${item.is_correct ? 'Correct' : 'Missed'} (${item.accuracy_score}%)
                    </span>
                </td>
                <td><span class="badge badge-mono">${item.efficiency_score}% Eff.</span></td>
            </tr>
        `).join('');
    }
};
