/**
 * Multimodal Viewer Component (Labs & Imaging)
 */
const MultimodalViewer = {
    selectedStudyIndex: 0,

    init() {
        State.subscribe((event, data) => {
            if (event === 'patientLoaded' || event === 'modeChanged') {
                this.render();
            }
        });
    },

    render() {
        const full = State.currentPatientFull;
        const trainee = State.currentTraineeView;
        if (!full || !trainee) return;

        const isSupervisor = State.isSupervisorMode;

        // Render Labs Table
        const labs = isSupervisor ? full.lab_history : trainee.available_labs;
        const tbody = document.getElementById('lab-results-tbody');

        if (!labs || labs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted" style="padding:24px;">
                        No laboratory tests have been ordered yet. Place orders via the Interactive Consultation tab or switch to Supervisor Mode.
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = labs.map(lab => {
                const unc = lab.uncertainty;
                const statusBadge = lab.is_abnormal ? 
                    `<span class="badge badge-warning">Abnormal</span>` : 
                    `<span class="badge badge-success">Normal</span>`;
                const evLevel = lab.evidence_ids && lab.evidence_ids.length > 0 ? 'Level A (Guideline)' : 'Expert Prior';

                return `
                    <tr class="${lab.is_abnormal ? 'abnormal-row' : ''}">
                        <td><strong>${lab.test_name}</strong></td>
                        <td class="${lab.is_abnormal ? 'highlight-cyan' : ''}">${lab.value}</td>
                        <td>${lab.unit}</td>
                        <td>${lab.ref_low} – ${lab.ref_high}</td>
                        <td style="font-family:var(--font-mono); font-size:0.75rem;">[${unc.ci_95_low}, ${unc.ci_95_high}]</td>
                        <td>${statusBadge}</td>
                        <td><span class="badge badge-mono">${evLevel}</span></td>
                    </tr>
                `;
            }).join('');
        }

        // Draw Biomarker Plot for first abnormal lab
        const canvas = document.getElementById('canvas-biomarker-plot');
        const primaryLab = labs.find(l => l.is_abnormal) || labs[0];
        ChartRenderer.renderBiomarkerPlot(canvas, primaryLab);

        // Render Imaging Studies
        const studies = isSupervisor ? full.imaging_studies : trainee.available_imaging;
        const tabsBox = document.getElementById('imaging-study-tabs');
        const detailsBox = document.getElementById('imaging-study-details');
        const svgViewport = document.getElementById('svg-slice-viewport');

        if (!studies || studies.length === 0) {
            tabsBox.innerHTML = '';
            detailsBox.innerHTML = `<p class="text-muted" style="padding:20px;">No imaging examinations have been ordered yet.</p>`;
            svgViewport.innerHTML = `<p class="text-muted" style="padding:40px;">Imaging unperformed. Order scans through clinical workstation.</p>`;
            return;
        }

        if (this.selectedStudyIndex >= studies.length) {
            this.selectedStudyIndex = 0;
        }

        tabsBox.innerHTML = studies.map((st, i) => `
            <button class="imaging-tab-btn ${i === this.selectedStudyIndex ? 'active' : ''}" data-idx="${i}">
                ${st.acronym} (${st.anatomical_region})
            </button>
        `).join('');

        tabsBox.querySelectorAll('.imaging-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.selectedStudyIndex = parseInt(btn.getAttribute('data-idx'));
                this.render();
            });
        });

        const activeStudy = studies[this.selectedStudyIndex];
        if (activeStudy) {
            detailsBox.innerHTML = `
                <div class="imaging-report-box">
                    <div class="report-section">
                        <h5>Modality & Anatomical Region</h5>
                        <p><strong>${activeStudy.modality}</strong> — ${activeStudy.anatomical_region}</p>
                    </div>
                    <div class="report-section">
                        <h5>Standardized Radiology Findings</h5>
                        <p>${activeStudy.acr_findings}</p>
                    </div>
                    <div class="report-section">
                        <h5>Radiology Impression</h5>
                        <p style="color:#e2e8f0; font-weight:600;">${activeStudy.radiology_impression.replace(/\n/g, '<br>')}</p>
                    </div>
                    <div class="report-section">
                        <h5>Pathological Signs Identified</h5>
                        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:4px;">
                            ${activeStudy.pathological_signs.map(s => `<span class="badge badge-purple">${s}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;

            ImagingRenderer.renderSliceSVG(svgViewport, activeStudy);
        }
    }
};
