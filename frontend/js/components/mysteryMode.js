/**
 * Clinical Mystery Mode Component
 *
 * Interactive clinical diagnostic challenge with difficulty tiers,
 * blinded consultations, financial & turnaround time tracking,
 * multi-factorial scoring, and educational debriefing.
 */
const MysteryMode = {
    activeSession: null,
    pricingCatalog: {},
    inquiryHistory: [],
    debriefingReport: null,

    async init() {
        this.bindEvents();
        try {
            this.pricingCatalog = await API.getInvestigationPricingCatalog();
            this.populatePricingCatalog();
        } catch (e) {
            console.warn('Could not load mystery pricing catalog:', e);
        }
    },

    bindEvents() {
        // Start challenge button
        document.getElementById('btn-start-mystery-case')?.addEventListener('click', () => {
            this.handleStartSession();
        });

        // Dialogue inquiry form
        document.getElementById('form-mystery-inquiry')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendInquiry();
        });

        // Quick inquiry suggestion chips
        document.querySelectorAll('.mystery-inquiry-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                const input = document.getElementById('input-mystery-inquiry');
                if (input) input.value = query;
                this.handleSendInquiry();
            });
        });

        // Order investigation button
        document.getElementById('btn-order-mystery-test')?.addEventListener('click', () => {
            this.handleOrderInvestigation();
        });

        // Final diagnosis submission form
        document.getElementById('form-mystery-submission')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmitDiagnosis();
        });

        // Play another case
        document.getElementById('btn-mystery-play-again')?.addEventListener('click', () => {
            document.getElementById('mystery-debriefing-card')?.classList.add('hidden');
            document.getElementById('mystery-active-workstation')?.classList.add('hidden');
            document.getElementById('mystery-intake-selector')?.classList.remove('hidden');
        });
    },

    async render() {
        if (State.currentUser?.role === 'supervisor') {
            document.getElementById('mystery-supervisor-section')?.classList.remove('hidden');
            await this.loadSupervisorHistory();
        } else {
            document.getElementById('mystery-supervisor-section')?.classList.add('hidden');
        }
    },

    populatePricingCatalog() {
        const select = document.getElementById('select-mystery-investigation');
        if (!select || !this.pricingCatalog) return;

        let options = '<option value="" disabled selected>Select diagnostic investigation to order...</option>';
        Object.entries(this.pricingCatalog).forEach(([code, item]) => {
            const isImaging = ['MRI', 'SLIT', 'US', 'XR', 'ECHO'].some(prefix => code.startsWith(prefix));
            const invType = isImaging ? 'imaging' : 'lab';
            options += `
                <option value="${code}" data-type="${invType}">
                    ${item.name} &bull; $${item.cost} &bull; Turnaround: ${item.hours}h
                </option>
            `;
        });
        select.innerHTML = options;
    },

    async handleStartSession() {
        const difficulty = document.getElementById('select-mystery-difficulty')?.value || 'intermediate';
        const traineeId = State.currentUser?.trainee_id || 'TR-8041';
        const traineeEmail = State.currentUser?.email || 'TR-8041@ggmail.com';

        try {
            App.showToast(`Starting ${difficulty} clinical mystery case...`);
            this.activeSession = await API.startMysterySession({
                difficulty: difficulty,
                trainee_id: traineeId,
                trainee_email: traineeEmail
            });

            this.inquiryHistory = [];
            this.debriefingReport = null;

            document.getElementById('mystery-intake-selector')?.classList.add('hidden');
            document.getElementById('mystery-debriefing-card')?.classList.add('hidden');
            document.getElementById('mystery-active-workstation')?.classList.remove('hidden');

            this.renderActiveSessionView();
            App.showToast(`Blinded case initialized. Chief complaint ready for interview.`);
        } catch (e) {
            console.error('Failed to start mystery session:', e);
            App.showToast(`Error: ${e.message}`);
        }
    },

    renderActiveSessionView() {
        if (!this.activeSession) return;
        const s = this.activeSession;

        // Session Header
        const sessionBadge = document.getElementById('mystery-session-id-badge');
        if (sessionBadge) sessionBadge.textContent = s.session_id;

        const diffBadge = document.getElementById('mystery-difficulty-badge');
        if (diffBadge) diffBadge.textContent = s.difficulty.toUpperCase();

        // Economics & Turnaround
        this.updateEconomicsDisplay();

        // Patient Intake Demographics & Chief Complaint
        const demoEl = document.getElementById('mystery-patient-demographics');
        if (demoEl) demoEl.textContent = `${s.age_years || 28}yo ${s.biological_sex || 'Patient'}, ${s.ethnicity || 'Unknown'}`;

        const complaintEl = document.getElementById('mystery-chief-complaint');
        if (complaintEl) complaintEl.textContent = s.chief_complaint || 'Presents for clinical evaluation.';

        const examEl = document.getElementById('mystery-physical-exam');
        if (examEl) {
            const sympTexts = (s.available_symptoms || []).map(symp => `${symp.name} (${symp.severity})`).join(', ');
            examEl.textContent = sympTexts ? `Initial findings: ${sympTexts}` : 'Baseline physical exam recorded. Proceed to interview.';
        }

        // Vitals
        const vitalsEl = document.getElementById('mystery-vitals');
        if (vitalsEl) {
            vitalsEl.textContent = `Patient ID: ${s.patient_id} | Status: ${s.status}`;
        }

        // Investigations Ordered List
        this.renderInvestigationsTable();
    },

    updateEconomicsDisplay() {
        if (!this.activeSession) return;
        const s = this.activeSession;

        const budgetEl = document.getElementById('mystery-budget-spent');
        if (budgetEl) budgetEl.textContent = `$${(s.accumulated_cost_usd || 0).toFixed(0)}`;

        const turnaroundEl = document.getElementById('mystery-turnaround-days');
        if (turnaroundEl) turnaroundEl.textContent = `${(s.accumulated_turnaround_hours || 0).toFixed(1)} Hours`;

        const inquiriesEl = document.getElementById('mystery-inquiries-count');
        if (inquiriesEl) inquiriesEl.textContent = `${this.inquiryHistory.length} Questions`;
    },

    async handleSendInquiry() {
        const input = document.getElementById('input-mystery-inquiry');
        const text = input?.value.trim();
        if (!text || !this.activeSession) return;

        try {
            const res = await API.sendMysteryInquiry(this.activeSession.session_id, text);
            this.inquiryHistory.push({ question: text, response: res.avatar_response });
            input.value = '';

            // Update dialogue transcript
            this.renderInquiryTranscript();

            // Refresh session economics
            this.activeSession = await API.getMysterySession(this.activeSession.session_id);
            this.updateEconomicsDisplay();
        } catch (e) {
            console.error('Inquiry failed:', e);
            App.showToast(`Inquiry error: ${e.message}`);
        }
    },

    renderInquiryTranscript() {
        const box = document.getElementById('mystery-dialogue-history');
        if (!box) return;

        box.innerHTML = this.inquiryHistory.map(item => `
            <div class="dialogue-exchange" style="margin-bottom: 12px; font-size: 0.85rem;">
                <div class="clinician-msg" style="padding: 8px 12px; background: rgba(51, 65, 85, 0.08); border-left: 3px solid var(--accent-cyan); border-radius: var(--radius-sm); margin-bottom: 4px;">
                    <strong>👨‍⚕️ Clinician:</strong> ${item.question}
                </div>
                <div class="avatar-msg" style="padding: 8px 12px; background: var(--bg-surface); border-left: 3px solid var(--accent-purple); border-radius: var(--radius-sm);">
                    <strong>🧑 Patient Avatar:</strong> ${item.response}
                </div>
            </div>
        `).join('');
        box.scrollTop = box.scrollHeight;
    },

    async handleOrderInvestigation() {
        const select = document.getElementById('select-mystery-investigation');
        const code = select?.value;
        if (!code || !this.activeSession) {
            App.showToast('Select a diagnostic investigation first');
            return;
        }

        const selectedOption = select.options[select.selectedIndex];
        const invType = selectedOption.getAttribute('data-type') || 'lab';

        try {
            App.showToast(`Ordering ${code}...`);
            const item = await API.orderMysteryInvestigation(this.activeSession.session_id, invType, code);
            App.showToast(`Order fulfilled: ${item.name}`);

            this.activeSession = await API.getMysterySession(this.activeSession.session_id);
            this.updateEconomicsDisplay();
            this.renderInvestigationsTable();
        } catch (e) {
            console.error('Order failed:', e);
            App.showToast(`Failed to order: ${e.message}`);
        }
    },

    renderInvestigationsTable() {
        const tbody = document.getElementById('tbody-mystery-investigations');
        if (!tbody || !this.activeSession) return;

        const items = this.activeSession.ordered_investigations || [];
        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-muted text-center">No investigations ordered yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = items.map(it => `
            <tr>
                <td><strong>${it.name}</strong><br><span style="font-size:0.7rem; font-family:var(--font-mono); color:var(--text-muted);">${it.code_or_acronym}</span></td>
                <td><span class="badge badge-mono">${it.modality}</span></td>
                <td style="font-family: var(--font-mono); font-weight: 700; color: ${it.is_abnormal ? 'var(--accent-crimson)' : 'var(--accent-cyan)'};">${it.result_summary}</td>
                <td style="font-size: 0.75rem;"><span class="badge ${it.is_abnormal ? 'badge-danger' : 'badge-success'}">${it.is_abnormal ? 'ABNORMAL' : 'NORMAL'}</span></td>
                <td><span class="badge badge-mono">$${it.simulated_cost_usd} (+${it.turnaround_hours}h)</span></td>
            </tr>
        `).join('');
    },

    async handleSubmitDiagnosis() {
        if (!this.activeSession) return;

        const primaryDiagnosisText = document.getElementById('select-mystery-primary-diagnosis')?.value;
        const differentialsStr = document.getElementById('input-mystery-differentials')?.value || '';
        const rationale = document.getElementById('textarea-mystery-rationale')?.value || 'Clinical correlation with cardinal findings.';
        const management = document.getElementById('textarea-mystery-management')?.value || '';

        if (!primaryDiagnosisText) {
            App.showToast('Please select your primary diagnosis');
            return;
        }

        // Map text to disease ID
        let diseaseId = 'wilson_disease';
        if (primaryDiagnosisText.toLowerCase().includes('wilson')) diseaseId = 'wilson_disease';
        else if (primaryDiagnosisText.toLowerCase().includes('fabry')) diseaseId = 'fabry_disease';
        else if (primaryDiagnosisText.toLowerCase().includes('gaucher')) diseaseId = 'gaucher_disease';
        else diseaseId = primaryDiagnosisText.toLowerCase().replace(/[^a-z0-9]/g, '_');

        const differentialsList = differentialsStr.split(',').map(s => s.trim()).filter(Boolean);
        const differentialsObjList = differentialsList.map(d => ({ [d]: 0.5 }));

        try {
            App.showToast('Evaluating clinical formulation against ground truth...');
            this.debriefingReport = await API.submitMysteryDiagnosis({
                session_id: this.activeSession.session_id,
                predicted_disease_id: diseaseId,
                predicted_disease_name: primaryDiagnosisText,
                confidence_score: 0.95,
                differential_diagnoses: differentialsObjList,
                clinical_justification: rationale,
                management_plan: management
            });

            this.renderDebriefingReport(this.debriefingReport);
            App.showToast('Mystery case completed! Educational debriefing unmasked.');
        } catch (e) {
            console.error('Submission failed:', e);
            App.showToast(`Submission error: ${e.message}`);
        }
    },

    renderDebriefingReport(rep) {
        document.getElementById('mystery-active-workstation')?.classList.add('hidden');
        const debriefCard = document.getElementById('mystery-debriefing-card');
        if (!debriefCard) return;
        debriefCard.classList.remove('hidden');

        // Unmasked Ground Truth Banner
        const truthDiseaseEl = document.getElementById('debrief-ground-truth-disease');
        if (truthDiseaseEl) truthDiseaseEl.textContent = rep.ground_truth_disease_name;

        const truthGeneEl = document.getElementById('debrief-ground-truth-gene');
        if (truthGeneEl) truthGeneEl.textContent = `${rep.debriefing?.omim_id || 'OMIM'} &bull; ${rep.ground_truth_disease_id}`;

        // Scorecard KPIs
        const card = rep.scorecard;
        const accEl = document.getElementById('debrief-accuracy-badge');
        if (accEl) {
            accEl.textContent = card.is_top1_correct ? 'CORRECT DIAGNOSIS (100%)' : 'INCORRECT DIAGNOSIS (0%)';
            accEl.className = card.is_top1_correct ? 'badge badge-success' : 'badge badge-danger';
        }

        const scoreCostEl = document.getElementById('debrief-score-cost');
        if (scoreCostEl) scoreCostEl.textContent = `${card.cost_efficiency_score.toFixed(0)}/100`;

        const scoreTurnaroundEl = document.getElementById('debrief-score-turnaround');
        if (scoreTurnaroundEl) scoreTurnaroundEl.textContent = `${card.accuracy_score.toFixed(0)}/100`;

        const scoreParsimonyEl = document.getElementById('debrief-score-parsimony');
        if (scoreParsimonyEl) scoreParsimonyEl.textContent = `${card.diagnostic_parsimony_score.toFixed(0)}/100`;

        const scoreMasteryEl = document.getElementById('debrief-score-mastery');
        if (scoreMasteryEl) scoreMasteryEl.textContent = `${card.overall_clinical_score.toFixed(0)}%`;

        // Educational Debriefing Text
        const debrief = rep.debriefing;
        const cardinalBox = document.getElementById('debrief-cardinal-clues');
        if (cardinalBox && debrief.pathognomonic_findings) {
            cardinalBox.innerHTML = debrief.pathognomonic_findings.map(c => `<li>🔍 ${c}</li>`).join('');
        }

        const wastefulBox = document.getElementById('debrief-wasteful-tests');
        if (wastefulBox) {
            if (debrief.common_pitfalls_avoided_or_committed && debrief.common_pitfalls_avoided_or_committed.length > 0) {
                wastefulBox.innerHTML = debrief.common_pitfalls_avoided_or_committed.map(t => `<li>⚠️ ${t}</li>`).join('');
            } else {
                wastefulBox.innerHTML = `<li class="text-success">✅ Zero unnecessary investigations ordered. Excellent parsimony!</li>`;
            }
        }

        const pathwayEl = document.getElementById('debrief-guideline-pathway');
        if (pathwayEl) pathwayEl.textContent = debrief.clinical_takeaway || debrief.phenotype_summary;

        // Literature Citations
        const refsBox = document.getElementById('debrief-literature-refs');
        if (refsBox && debrief.relevant_guidelines) {
            refsBox.innerHTML = debrief.relevant_guidelines.map(c => `
                <div class="citation-chip card glass-card" style="padding: 8px 12px; margin-bottom: 6px; font-size: 0.8rem;">
                    <strong>${c.title}</strong> &bull; <em>${c.journal} (${c.year})</em>
                    ${c.pmid ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${c.pmid}/" target="_blank" rel="noopener noreferrer" class="badge badge-mono pmid-link" style="margin-left: 6px;">PMID: ${c.pmid}</a>` : ''}
                </div>
            `).join('');
        }
    },

    async loadSupervisorHistory() {
        const tbody = document.getElementById('tbody-supervisor-mystery-history');
        if (!tbody) return;

        try {
            const records = await API.getSupervisorMysterySessions();
            if (records.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-muted text-center">No completed mystery sessions recorded.</td></tr>`;
                return;
            }

            tbody.innerHTML = records.map(r => `
                <tr>
                    <td><strong style="font-family:var(--font-mono);">${r.session_id}</strong></td>
                    <td><span class="badge badge-cyan">${r.trainee_id || 'Trainee'}</span></td>
                    <td>${r.ground_truth_disease_name}</td>
                    <td>
                        <span class="badge ${r.scorecard.is_top1_correct ? 'badge-success' : 'badge-danger'}">
                            ${r.scorecard.is_top1_correct ? 'CORRECT' : 'INCORRECT'}
                        </span>
                    </td>
                    <td><strong>${r.scorecard.overall_clinical_score.toFixed(0)}%</strong></td>
                    <td>$${r.total_cost_usd} (${r.investigations_count} tests)</td>
                    <td>${r.total_turnaround_hours.toFixed(1)} hours</td>
                </tr>
            `).join('');
        } catch (e) {
            console.warn('Could not load supervisor mystery records:', e);
        }
    }
};
