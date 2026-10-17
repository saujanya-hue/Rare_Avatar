/**
 * Clinical What-If Lab Component
 *
 * Branching simulation engine with immutable patient snapshots, counterfactual interventions,
 * multi-branch trajectory tracking, and side-by-side comparison.
 */
const WhatIfLab = {
    patientBranches: [],
    selectedBranchIds: new Set(),
    activeComparison: null,

    async init() {
        this.bindEvents();
        State.subscribe((event, data) => {
            if (event === 'patientLoaded' && State.activeTab === 'what-if') {
                this.render();
            }
        });
    },

    bindEvents() {
        // Fork branch form submit
        document.getElementById('form-create-what-if-branch')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreateBranch();
        });

        // Adherence slider
        const adhSlider = document.getElementById('input-what-if-adherence');
        adhSlider?.addEventListener('input', (e) => {
            const lbl = document.getElementById('label-what-if-adherence-val');
            if (lbl) lbl.textContent = `${e.target.value}%`;
        });

        // Compare Selected Branches button
        document.getElementById('btn-compare-what-if-branches')?.addEventListener('click', () => {
            this.handleCompareSelectedBranches();
        });

        // Quick Preset Buttons
        document.getElementById('btn-preset-adherent')?.addEventListener('click', () => {
            const inputName = document.getElementById('input-what-if-branch-name');
            const slider = document.getElementById('input-what-if-adherence');
            const lbl = document.getElementById('label-what-if-adherence-val');
            if (inputName) inputName.value = 'Optimal Guideline Adherence (95%)';
            if (slider) slider.value = 95;
            if (lbl) lbl.textContent = '95%';
        });

        document.getElementById('btn-preset-untreated')?.addEventListener('click', () => {
            const inputName = document.getElementById('input-what-if-branch-name');
            const slider = document.getElementById('input-what-if-adherence');
            const lbl = document.getElementById('label-what-if-adherence-val');
            if (inputName) inputName.value = 'Untreated Natural History (0%)';
            if (slider) slider.value = 0;
            if (lbl) lbl.textContent = '0%';
        });
    },

    async render() {
        this.updateActivePatientHeader();
        await this.loadPatientBranches();
        this.populateScenarioDropdown();
    },

    updateActivePatientHeader() {
        const idBadge = document.getElementById('what-if-patient-id');
        const diseaseBadge = document.getElementById('what-if-patient-disease');
        const monthBadge = document.getElementById('what-if-patient-month');

        if (!State.currentPatient) {
            if (idBadge) idBadge.textContent = 'No Active Avatar';
            return;
        }

        if (idBadge) idBadge.textContent = State.currentPatient.patient_id;
        if (diseaseBadge) diseaseBadge.textContent = State.currentPatient.disease_name;
        if (monthBadge) monthBadge.textContent = `Month ${State.currentPatient.current_simulation_month}`;
    },

    populateScenarioDropdown() {
        const select = document.getElementById('select-what-if-scenario');
        if (!select || !State.currentPatient) return;

        const disease = State.currentPatient.disease_id;
        let options = '';

        if (disease === 'wilson_disease') {
            options = `
                <option value="D-Penicillamine" data-type="Targeted Therapy" selected>D-Penicillamine Chelation (Copper Excretion)</option>
                <option value="Trientine" data-type="Alternative Agent">Trientine Dihydrochloride Chelation</option>
                <option value="Zinc Acetate" data-type="Maintenance Therapy">Zinc Acetate (Metallothionein Induction)</option>
                <option value="Untreated" data-type="Untreated Natural History">Untreated Natural History (Progressive Copper Overload)</option>
            `;
        } else if (disease === 'fabry_disease') {
            options = `
                <option value="Agalsidase Beta" data-type="Targeted Therapy" selected>Agalsidase Beta Enzyme Replacement (1 mg/kg IV q2w)</option>
                <option value="Miglustat" data-type="Alternative Agent">Miglustat Pharmacological Chaperone Therapy</option>
                <option value="Untreated" data-type="Untreated Natural History">Untreated Natural History (Lyso-Gb3 Accumulation)</option>
            `;
        } else if (disease === 'gaucher_disease') {
            options = `
                <option value="Imiglucerase" data-type="Targeted Therapy" selected>Imiglucerase Enzyme Replacement (60 U/kg IV q2w)</option>
                <option value="Eliglustat" data-type="Alternative Agent">Eliglustat Substrate Reduction Therapy</option>
                <option value="Untreated" data-type="Untreated Natural History">Untreated Natural History (Hepatosplenomegaly & Cytopenias)</option>
            `;
        } else {
            options = `<option value="First-Line Therapy" data-type="Targeted Therapy" selected>Standard Recommended Therapy</option>`;
        }

        select.innerHTML = options;
    },

    async loadPatientBranches() {
        const container = document.getElementById('what-if-branches-list');
        if (!container) return;

        if (!State.currentPatientId) {
            container.innerHTML = `<div class="text-muted p-3">Select a patient avatar first.</div>`;
            return;
        }

        try {
            this.patientBranches = await API.listPatientBranches(State.currentPatientId);
            if (this.patientBranches.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-card text-center" style="padding: 24px;">
                        <span style="font-size: 2rem;">🌿</span>
                        <p class="text-muted" style="margin-top: 8px;">No simulation branches forked yet. Create your first branch above!</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = this.patientBranches.map(branch => {
                const isSelected = this.selectedBranchIds.has(branch.branch_id);
                const trajectoryCount = branch.trajectory?.length || 0;
                return `
                    <div class="card glass-card branch-card" style="padding: 16px; margin-bottom: 12px; border-left: 4px solid var(--accent-purple);">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <label style="display: flex; align-items: center; gap: 8px; font-weight: 700; cursor: pointer;">
                                    <input type="checkbox" class="check-select-branch" data-branch-id="${branch.branch_id}" ${isSelected ? 'checked' : ''}>
                                    <span style="font-size: 1rem;">${branch.branch_name}</span>
                                </label>
                                <div style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted); margin-top: 2px;">
                                    Branch ID: ${branch.branch_id}
                                </div>
                            </div>
                            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                                <span class="badge badge-mono">Month: ${branch.current_month}</span>
                                <span class="badge badge-info">${branch.intervention_type}</span>
                                <span class="badge badge-cyan">${trajectoryCount} Points</span>
                            </div>
                        </div>

                        <div style="margin-top: 10px; font-size: 0.82rem; color: var(--text-secondary);">
                            <strong>Agent / Regimen:</strong> <code>${branch.intervention_agent || 'Standard'}</code>
                        </div>

                        <div class="branch-controls-row" style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: space-between;">
                            <div class="btn-group">
                                <button type="button" class="btn btn-sm btn-secondary btn-advance-branch" data-branch-id="${branch.branch_id}" data-months="3">+3 Months</button>
                                <button type="button" class="btn btn-sm btn-secondary btn-advance-branch" data-branch-id="${branch.branch_id}" data-months="6">+6 Months</button>
                                <button type="button" class="btn btn-sm btn-secondary btn-advance-branch" data-branch-id="${branch.branch_id}" data-months="12">+12 Months</button>
                            </div>
                            <div class="export-links" style="display: flex; gap: 6px;">
                                <a href="/api/what-if/branches/${branch.branch_id}/export?format=csv" target="_blank" class="btn btn-sm btn-outline-cyan">📥 CSV</a>
                                <a href="/api/what-if/branches/${branch.branch_id}/export?format=json" target="_blank" class="btn btn-sm btn-outline-cyan">📥 JSON</a>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            // Bind checkbox events
            container.querySelectorAll('.check-select-branch').forEach(cb => {
                cb.addEventListener('change', (e) => {
                    const bid = e.target.getAttribute('data-branch-id');
                    if (e.target.checked) this.selectedBranchIds.add(bid);
                    else this.selectedBranchIds.delete(bid);
                });
            });

            // Bind advance branch buttons
            container.querySelectorAll('.btn-advance-branch').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const bid = btn.getAttribute('data-branch-id');
                    const months = parseInt(btn.getAttribute('data-months'));
                    await this.handleAdvanceBranch(bid, months);
                });
            });

        } catch (e) {
            console.error('Failed to load branches:', e);
            container.innerHTML = `<div class="text-danger p-3">Error loading branches: ${e.message}</div>`;
        }
    },

    async handleCreateBranch() {
        if (!State.currentPatientId) {
            App.showToast('Please select an active patient avatar first');
            return;
        }

        const branchName = document.getElementById('input-what-if-branch-name')?.value.trim() || 'Counterfactual Branch';
        const select = document.getElementById('select-what-if-scenario');
        const agent = select?.value || 'First-Line Therapy';
        const selectedOption = select?.options[select.selectedIndex];
        const type = selectedOption?.getAttribute('data-type') || 'Targeted Therapy';
        const currentMonth = State.currentPatient?.current_simulation_month || 0;

        try {
            const config = {
                patient_id: State.currentPatientId,
                branch_name: branchName,
                intervention_type: type,
                intervention_agent: agent,
                origin_month: currentMonth,
                notes: `Forked from active patient ${State.currentPatientId} at month ${currentMonth}`
            };

            const newBranch = await API.createWhatIfBranch(config);
            this.selectedBranchIds.add(newBranch.branch_id);
            App.showToast(`Branch "${newBranch.branch_name}" created successfully!`);
            await this.loadPatientBranches();
        } catch (e) {
            console.error('Failed to create branch:', e);
            App.showToast(`Failed: ${e.message}`);
        }
    },

    async handleAdvanceBranch(branchId, months) {
        try {
            App.showToast(`Advancing branch forward +${months} months...`);
            await API.advanceWhatIfBranch(branchId, months);
            App.showToast(`Advanced +${months} months successfully!`);
            await this.loadPatientBranches();
            if (this.selectedBranchIds.has(branchId) && this.selectedBranchIds.size >= 1) {
                await this.handleCompareSelectedBranches();
            }
        } catch (e) {
            console.error('Failed to advance branch:', e);
            App.showToast(`Advance failed: ${e.message}`);
        }
    },

    async handleCompareSelectedBranches() {
        if (this.selectedBranchIds.size === 0) {
            this.patientBranches.forEach(b => this.selectedBranchIds.add(b.branch_id));
        }

        const branchIds = Array.from(this.selectedBranchIds);
        if (branchIds.length === 0) {
            App.showToast('No branches available to compare');
            return;
        }

        const compContainer = document.getElementById('what-if-comparison-container');
        if (!compContainer) return;
        compContainer.classList.remove('hidden');

        try {
            this.activeComparison = await API.compareWhatIfBranches(State.currentPatientId, branchIds);
            this.renderComparisonReport(this.activeComparison);
        } catch (e) {
            console.error('Comparison failed:', e);
            App.showToast(`Comparison failed: ${e.message}`);
        }
    },

    renderComparisonReport(report) {
        const tableBody = document.getElementById('tbody-what-if-comparison');
        if (tableBody && report.comparative_metrics) {
            tableBody.innerHTML = report.comparative_metrics.map(rec => `
                <tr>
                    <td><strong>${rec.branch_name}</strong><br><span style="font-size:0.7rem; font-family:var(--font-mono); color:var(--text-muted);">${rec.branch_id}</span></td>
                    <td><code>${rec.intervention_agent}</code> (${rec.intervention_type})</td>
                    <td><span class="badge badge-info">${rec.duration_months} Months</span></td>
                    <td><span class="badge badge-mono">${rec.biomarker_start} &rarr; ${rec.biomarker_end} ${rec.biomarker_unit}</span></td>
                    <td><span class="badge ${rec.biomarker_delta <= 0 ? 'badge-success' : 'badge-danger'}">${rec.biomarker_delta > 0 ? '+' : ''}${rec.biomarker_delta} ${rec.biomarker_unit}</span></td>
                    <td style="font-size:0.8rem;">${rec.terminal_clinical_status}</td>
                </tr>
            `).join('');
        }

        // Render trajectory chart
        this.renderTrajectoryCanvas(report);
    },

    renderTrajectoryCanvas(report) {
        const canvas = document.getElementById('canvas-what-if-trajectories');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const width = canvas.width = canvas.parentElement.clientWidth || 600;
        const height = canvas.height = 240;

        ctx.clearRect(0, 0, width, height);

        // Draw axes and labels
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(50, 20);
        ctx.lineTo(50, height - 30);
        ctx.lineTo(width - 20, height - 30);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = '10px sans-serif';
        ctx.fillText('Month 0', 45, height - 15);
        ctx.fillText(report.clinical_recommendation ? `Recommendation: ${report.clinical_recommendation}` : 'Longitudinal Trajectory Comparison', 55, 15);

        const colors = ['#334155', '#7c3aed', '#10b981', '#f59e0b', '#ef4444'];
        const branches = Object.values(report.branches || {});

        branches.forEach((b, idx) => {
            const color = colors[idx % colors.length];
            const traj = b.trajectory || [];
            if (traj.length === 0) return;

            ctx.strokeStyle = color;
            ctx.lineWidth = 2.5;
            ctx.beginPath();

            traj.forEach((pt, pIdx) => {
                const x = Math.min(width - 50, 50 + (pt.month || 0) * 20);
                const val = pt.primary_biomarker_value;
                const y = Math.max(30, Math.min(height - 40, height - 40 - (val / 3)));

                if (pIdx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);

                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();
            });

            ctx.stroke();

            // Label at terminal point
            const lastPt = traj[traj.length - 1];
            const lx = Math.min(width - 120, 50 + (lastPt.month || 0) * 20);
            const ly = Math.max(30, Math.min(height - 40, height - 40 - (lastPt.primary_biomarker_value / 3)));
            ctx.fillStyle = color;
            ctx.fillText(`${b.branch_name} (${lastPt.primary_biomarker_value})`, lx + 6, ly - 4);
        });
    }
};
