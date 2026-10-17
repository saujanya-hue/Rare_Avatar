/**
 * Supervisor Trainee Oversight Component
 * Allows clinical supervisors to monitor trainee diagnostic accuracy,
 * test ordering efficiency, missed cardinal hallmarks, and debriefing notes.
 */
const SupervisorOversight = {
    recordsData: null,

    async init() {
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById('btn-refresh-oversight')?.addEventListener('click', async () => {
            await this.loadRecords();
            App.showToast('Trainee performance records refreshed.');
        });
    },

    async loadRecords() {
        try {
            const data = await API.getSupervisorTraineeRecords();
            this.recordsData = data;
            this.renderSummary(data.summary);
            this.renderTable(data.submissions);
        } catch (err) {
            console.error('Failed to load supervisor oversight records:', err);
        }
    },

    renderSummary(summary) {
        if (!summary) return;

        const countElem = document.getElementById('oversight-total-submissions');
        if (countElem) countElem.textContent = summary.total_trainee_submissions;

        const passElem = document.getElementById('oversight-pass-rate');
        if (passElem) passElem.textContent = `${summary.overall_pass_rate_pct}%`;

        const accElem = document.getElementById('oversight-avg-accuracy');
        if (accElem) accElem.textContent = `${summary.average_accuracy_score}%`;

        const effElem = document.getElementById('oversight-avg-efficiency');
        if (effElem) effElem.textContent = `${summary.average_test_efficiency}%`;
    },

    renderTable(submissions) {
        const tbody = document.getElementById('oversight-submissions-tbody');
        if (!tbody) return;

        if (!submissions || submissions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-muted" style="text-align:center;">No trainee submissions recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = submissions.map(sub => `
            <tr>
                <td><strong>${sub.submission_id}</strong></td>
                <td><span class="badge badge-cyan">👤 ${sub.trainee_id}</span></td>
                <td><span class="badge badge-mono">${sub.patient_id}</span></td>
                <td>${sub.primary_diagnosis}</td>
                <td><em>${sub.ground_truth_disease_name}</em></td>
                <td>
                    <span class="badge ${sub.is_correct ? 'badge-success' : 'badge-danger'}">
                        ${sub.is_correct ? 'PASSED' : 'MISSED'} (${sub.accuracy_score}%)
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-secondary btn-inspect-trainee-sub" data-subid="${sub.submission_id}">
                        Debriefing
                    </button>
                </td>
            </tr>
        `).join('');

        // Attach debriefing click listener
        tbody.querySelectorAll('.btn-inspect-trainee-sub').forEach(btn => {
            btn.addEventListener('click', () => {
                const subId = btn.getAttribute('data-subid');
                const sub = submissions.find(s => s.submission_id === subId);
                if (sub) this.openDebriefingModal(sub);
            });
        });
    },

    openDebriefingModal(sub) {
        let modal = document.getElementById('modal-debriefing-inspector');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal-debriefing-inspector';
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-dialog card glass-card" style="max-width: 620px;">
                    <div class="modal-header">
                        <div>
                            <h3 id="debrief-modal-title">Trainee Diagnostic Debriefing</h3>
                            <span id="debrief-modal-subid" class="badge badge-purple">SUBMISSION</span>
                        </div>
                        <button class="btn-close-modal" id="btn-close-debrief-modal">&times;</button>
                    </div>
                    <div class="modal-body" id="debrief-modal-body" style="padding: 20px; display: flex; flex-direction: column; gap: 14px;">
                        <!-- Dynamic Content -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" id="btn-close-debrief-footer">Close Debriefing</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            const closeModal = () => modal.classList.add('hidden');
            modal.querySelector('#btn-close-debrief-modal')?.addEventListener('click', closeModal);
            modal.querySelector('#btn-close-debrief-footer')?.addEventListener('click', closeModal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
        }

        const badgeSubId = modal.querySelector('#debrief-modal-subid');
        if (badgeSubId) badgeSubId.textContent = `${sub.submission_id} • Trainee: ${sub.trainee_id}`;

        const body = modal.querySelector('#debrief-modal-body');
        if (body) {
            body.innerHTML = `
                <div style="display: flex; gap: 12px; align-items: center;">
                    <span class="badge ${sub.is_correct ? 'badge-success' : 'badge-danger'}" style="font-size: 0.85rem; padding: 6px 12px;">
                        ${sub.is_correct ? '✅ PASSED — CORRECT PRIMARY' : '❌ FAILED — MISSED DIAGNOSIS'}
                    </span>
                    <span class="badge badge-mono">Score: ${sub.accuracy_score}%</span>
                    <span class="badge badge-cyan">Efficiency: ${sub.efficiency_score}%</span>
                </div>

                <div class="scorecard-detail-item" style="padding: 10px; background: var(--bg-secondary); border-radius: var(--radius-sm);">
                    <p style="font-size: 0.85rem; margin-bottom: 4px;"><strong>Submitted Diagnosis:</strong> ${sub.primary_diagnosis}</p>
                    <p style="font-size: 0.85rem; margin-bottom: 4px;"><strong>Ground Truth Disease:</strong> <span class="highlight-purple">${sub.ground_truth_disease_name}</span></p>
                    <p style="font-size: 0.8rem; color: var(--text-muted);">Avatar ID: ${sub.patient_id} &bull; Trainee Email: ${sub.trainee_email}</p>
                </div>

                <div>
                    <h4 style="font-size: 0.82rem; color: var(--accent-emerald); margin-bottom: 4px;">✓ Detected Key Hallmarks</h4>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">${sub.hallmarks_detected && sub.hallmarks_detected.length ? sub.hallmarks_detected.join(', ') : 'None'}</p>
                </div>

                <div>
                    <h4 style="font-size: 0.82rem; color: var(--accent-amber); margin-bottom: 4px;">⚠ Missed Cardinal Hallmarks / Underutilized Tests</h4>
                    <p style="font-size: 0.82rem; color: var(--text-secondary);">${sub.missed_hallmarks && sub.missed_hallmarks.length ? sub.missed_hallmarks.join(', ') : 'None'}</p>
                </div>

                <div class="scorecard-debrief-box">
                    <h4 style="font-size: 0.85rem; margin-bottom: 6px; color: var(--accent-purple);">👨‍🏫 Supervisor Evaluation Debriefing</h4>
                    <p style="font-size: 0.85rem; line-height: 1.5;">${sub.supervisor_debriefing}</p>
                </div>
            `;
        }

        modal.classList.remove('hidden');
    }
};
