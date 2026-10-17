/**
 * Clinical Consistency Guardian & Privacy Audit Component
 *
 * Implements automated 5-category clinical consistency validation:
 * 1. Physiological Constraints
 * 2. Cross-Modal Pathophysiology
 * 3. Temporal Dynamics
 * 4. Treatment-Model Coherence
 * 5. Evidence Grounding
 * Plus privacy and anti-memorization safeguards.
 */
const ValidationPrivacy = {
    currentReport: null,
    filterCategory: 'all',
    filterStatus: 'all',

    init() {
        this.bindEvents();
        State.subscribe((event, data) => {
            if (event === 'patientLoaded') {
                this.runAudit();
            }
        });
    },

    bindEvents() {
        document.getElementById('btn-re-run-audit')?.addEventListener('click', () => {
            this.runAudit();
        });

        // Category filter buttons
        document.querySelectorAll('.val-cat-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.val-cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterCategory = btn.getAttribute('data-cat');
                this.renderRulesTable();
            });
        });

        // Status filter buttons
        document.querySelectorAll('.val-status-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.val-status-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterStatus = btn.getAttribute('data-status');
                this.renderRulesTable();
            });
        });
    },

    async runAudit() {
        if (!State.currentPatientId) return;

        try {
            this.currentReport = await API.getValidationAudit(State.currentPatientId);
            this.renderReport(this.currentReport);
        } catch (e) {
            console.error('Validation audit failed:', e);
            App.showToast(`Audit failed: ${e.message}`);
        }
    },

    renderReport(rep) {
        if (!rep) return;
        this.currentReport = rep;

        // 1. Guardian Verdict Banner
        const verdictBanner = document.getElementById('guardian-verdict-banner');
        const verdictBadge = document.getElementById('guardian-verdict-badge');
        const verdictDesc = document.getElementById('guardian-verdict-desc');

        if (verdictBadge && rep.guardian_verdict) {
            verdictBadge.textContent = rep.guardian_verdict.replace(/_/g, ' ');
            const isPassing = rep.guardian_verdict === 'VERIFIED_CONSISTENT';
            const isWarning = rep.guardian_verdict === 'WARNINGS_DETECTED';

            if (isPassing) {
                verdictBadge.className = 'badge badge-success';
                if (verdictDesc) verdictDesc.textContent = 'All physiological, cross-modal, temporal, treatment, and evidence constraints validated across peer-reviewed guidelines.';
            } else if (isWarning) {
                verdictBadge.className = 'badge badge-warning';
                if (verdictDesc) verdictDesc.textContent = 'Non-critical atypical presentation or mild borderline deviations detected. Review recommended.';
            } else {
                verdictBadge.className = 'badge badge-danger';
                if (verdictDesc) verdictDesc.textContent = 'Critical clinical inconsistencies or cross-modal contamination detected. Patient avatar requires review.';
            }
        }

        // 2. High-level Metrics
        const statusEl = document.getElementById('val-status-label');
        if (statusEl) {
            statusEl.textContent = rep.overall_status.replace(/_/g, ' ');
            statusEl.className = rep.overall_status === 'AUTOMATED_CHECKS_PASSED' ? 'metric-val status-passed' : 'metric-val status-failed';
        }

        const checksEl = document.getElementById('val-checks-count');
        if (checksEl) checksEl.textContent = `${rep.passed_checks} / ${rep.total_checks}`;

        const ngramEl = document.getElementById('val-ngram-overlap');
        if (ngramEl) ngramEl.textContent = `${(rep.max_literature_ngram_overlap * 100).toFixed(1)}%`;

        const distEl = document.getElementById('val-ref-dist');
        if (distEl) distEl.textContent = rep.nearest_reference_patient_distance.toFixed(3);

        const privacyEl = document.getElementById('val-privacy-risk');
        if (privacyEl) {
            privacyEl.textContent = rep.overall_privacy_risk;
            privacyEl.className = rep.overall_privacy_risk.includes('LOW') ? 'metric-val status-passed' : 'metric-val status-failed';
        }

        // 3. Category Summaries (5 Categories)
        this.renderCategorySummaryChips(rep.category_summary || {});

        // 4. Expert Note
        const noteEl = document.getElementById('val-expert-note');
        if (noteEl) noteEl.textContent = rep.expert_validation_note || 'Automated multi-category consistency checks verified against ACMG, EASL, and European Gaucher Working Group consensus guidelines.';

        // 5. Clinical Rules Table with filters
        this.renderRulesTable();

        // 6. Privacy Checks Box
        this.renderPrivacyChecks(rep.privacy_audit_results || []);
    },

    renderCategorySummaryChips(summary) {
        const catMap = {
            'Physiological': { elId: 'cat-chip-physio', icon: '🫀' },
            'Cross-Modal': { elId: 'cat-chip-crossmodal', icon: '🧬' },
            'Temporal': { elId: 'cat-chip-temporal', icon: '⏱️' },
            'Treatment-Model': { elId: 'cat-chip-treatment', icon: '💊' },
            'Evidence-Grounding': { elId: 'cat-chip-evidence', icon: '📖' }
        };

        Object.entries(catMap).forEach(([catKey, cfg]) => {
            const chip = document.getElementById(cfg.elId);
            if (!chip) return;
            const data = summary[catKey] || { passed: 0, warning: 0, failed: 0, total: 0 };
            const isAllPass = data.failed === 0 && data.warning === 0;

            chip.innerHTML = `
                <span class="cat-chip-title">${cfg.icon} ${catKey}</span>
                <div class="cat-chip-stats">
                    <span class="badge ${isAllPass ? 'badge-success' : data.failed > 0 ? 'badge-danger' : 'badge-warning'}">
                        ${data.passed}/${data.total} Pass
                    </span>
                    ${data.failed > 0 ? `<span class="badge badge-danger">${data.failed} Fail</span>` : ''}
                    ${data.warning > 0 ? `<span class="badge badge-warning">${data.warning} Warn</span>` : ''}
                </div>
            `;
        });
    },

    renderRulesTable() {
        const rulesTbody = document.getElementById('clinical-rules-tbody');
        if (!rulesTbody || !this.currentReport) return;

        let items = this.currentReport.clinical_consistency_results || [];

        // Apply category filter
        if (this.filterCategory !== 'all') {
            items = items.filter(r => r.category === this.filterCategory);
        }

        // Apply status filter
        if (this.filterStatus === 'failed') {
            items = items.filter(r => !r.passed || r.status === 'FAILED');
        } else if (this.filterStatus === 'warning') {
            items = items.filter(r => r.status === 'WARNING');
        } else if (this.filterStatus === 'passed') {
            items = items.filter(r => r.passed && r.status === 'PASSED');
        }

        if (items.length === 0) {
            rulesTbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 20px;">No rule checks matching the selected filter.</td></tr>`;
            return;
        }

        rulesTbody.innerHTML = items.map(r => {
            let statusBadge = '';
            if (r.status === 'PASSED') {
                statusBadge = '<span class="badge badge-success">PASSED</span>';
            } else if (r.status === 'WARNING') {
                statusBadge = '<span class="badge badge-warning">WARNING</span>';
            } else {
                statusBadge = '<span class="badge badge-danger">FAILED</span>';
            }

            return `
                <tr>
                    <td>
                        <strong>${r.rule_name}</strong>
                        <div style="font-size:0.7rem; font-family:var(--font-mono); color:var(--text-muted);">${r.rule_id}</div>
                    </td>
                    <td><span class="badge badge-mono">${r.category}</span></td>
                    <td style="font-size:0.75rem; color:var(--text-secondary);">${r.expected_constraint}</td>
                    <td style="font-size:0.75rem; font-family:var(--font-mono); font-weight:600;">${r.observed_value}</td>
                    <td>${statusBadge}</td>
                    <td style="font-size:0.72rem; color:var(--text-muted);">${r.rule_source || 'Clinical Consensus'}</td>
                    <td style="font-size:0.75rem; color:var(--accent-cyan);">${r.suggested_action || 'None'}</td>
                </tr>
            `;
        }).join('');
    },

    renderPrivacyChecks(checks) {
        const privBox = document.getElementById('privacy-checks-box');
        if (!privBox) return;

        privBox.innerHTML = checks.map(p => `
            <div class="privacy-check-item">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:var(--text-primary); font-size:0.9rem;">${p.check_name}</strong>
                    <span class="badge ${p.passed ? 'badge-success' : 'badge-danger'}">
                        ${p.passed ? 'PASSED (SAFE)' : 'RISK DETECTED'}
                    </span>
                </div>
                <div style="font-size:0.82rem; color:var(--text-secondary); margin-top:4px; line-height:1.45;">
                    ${p.details}
                </div>
                <div style="font-size:0.75rem; font-family:var(--font-mono); color:var(--text-muted); margin-top:4px;">
                    Metric: <strong>${p.metric}</strong> | Computed: <strong>${p.computed_score}</strong> (Threshold: ${p.threshold})
                </div>
            </div>
        `).join('');
    }
};
