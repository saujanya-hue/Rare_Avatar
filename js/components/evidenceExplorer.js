/**
 * Evidence Explorer Component
 *
 * Grounding multimodal patient avatars in peer-reviewed PubMed literature,
 * providing interactive literature search, active avatar finding provenance,
 * and biomarker evidence catalogs.
 */
const EvidenceExplorer = {
    summary: null,
    catalog: [],
    searchResults: [],
    selectedDisease: 'all',
    searchQuery: '',

    async init() {
        this.bindEvents();
        State.subscribe((event, data) => {
            if (event === 'patientLoaded' && State.activeTab === 'evidence') {
                this.loadActivePatientProvenance();
            }
        });
    },

    bindEvents() {
        // Disease filter change
        document.getElementById('filter-evidence-disease')?.addEventListener('change', (e) => {
            this.selectedDisease = e.target.value;
            this.loadLiterature();
        });

        // Search input
        const searchInput = document.getElementById('input-evidence-search');
        let debounceTimer = null;
        searchInput?.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            this.searchQuery = e.target.value.trim();
            debounceTimer = setTimeout(() => {
                this.loadLiterature();
            }, 300);
        });

        // Refresh Provenance button
        document.getElementById('btn-refresh-patient-provenance')?.addEventListener('click', () => {
            this.loadActivePatientProvenance();
        });

        // Subtabs (Patient Provenance vs Literature Catalog vs Biomarker Catalog)
        document.querySelectorAll('.evidence-subtab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.evidence-subtab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const targetView = btn.getAttribute('data-view');
                document.getElementById('view-evidence-provenance')?.classList.toggle('hidden', targetView !== 'provenance');
                document.getElementById('view-evidence-catalog')?.classList.toggle('hidden', targetView !== 'catalog');
                document.getElementById('view-evidence-biomarkers')?.classList.toggle('hidden', targetView !== 'biomarkers');
            });
        });
    },

    async render() {
        await Promise.all([
            this.loadSummary(),
            this.loadLiterature(),
            this.loadActivePatientProvenance(),
            this.loadBiomarkerCatalog()
        ]);
    },

    async loadSummary() {
        try {
            this.summary = await API.getEvidenceSummary();
            this.renderSummary();
        } catch (e) {
            console.warn('Could not load evidence summary:', e);
        }
    },

    renderSummary() {
        if (!this.summary) return;
        const totalPubsEl = document.getElementById('kpi-evidence-pubs');
        if (totalPubsEl) totalPubsEl.textContent = this.summary.total_publications;

        const bioCountEl = document.getElementById('kpi-evidence-biomarkers');
        if (bioCountEl) bioCountEl.textContent = this.summary.supported_biomarkers_count;

        const tierChipsEl = document.getElementById('evidence-tier-chips');
        if (tierChipsEl && this.summary.evidence_tier_distribution) {
            tierChipsEl.innerHTML = Object.entries(this.summary.evidence_tier_distribution).map(([tier, count]) => `
                <span class="cohort-chip">
                    ${tier}: <strong>${count}</strong>
                </span>
            `).join('');
        }
    },

    async loadLiterature() {
        const container = document.getElementById('literature-articles-list');
        if (!container) return;

        try {
            let refs = [];
            if (this.searchQuery && this.searchQuery.length >= 2) {
                const disease = this.selectedDisease !== 'all' ? this.selectedDisease : null;
                refs = await API.searchEvidence(this.searchQuery, disease);
            } else if (this.selectedDisease !== 'all') {
                refs = await API.getEvidenceByDisease(this.selectedDisease);
            } else {
                refs = await API.listEvidence();
            }

            if (refs.length === 0) {
                container.innerHTML = `
                    <div class="empty-state-card text-center" style="padding: 30px;">
                        <span style="font-size: 2rem;">🔍</span>
                        <p class="text-muted" style="margin-top: 8px;">No PubMed references found matching your search query or filter.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = refs.map(ref => {
                const pmidUrl = `https://pubmed.ncbi.nlm.nih.gov/${ref.pmid}/`;
                const tierClass = ref.evidence_level.includes('Level 1') ? 'badge-success' : 'badge-info';
                return `
                    <div class="card glass-card article-card">
                        <div class="article-top">
                            <span class="badge ${tierClass}">${ref.evidence_level}</span>
                            <a href="${pmidUrl}" target="_blank" rel="noopener noreferrer" class="badge badge-mono pmid-link" title="Open citation on PubMed">
                                🔗 PMID: ${ref.pmid}
                            </a>
                        </div>
                        <h4 class="article-title" style="margin-top: 6px;">${ref.title}</h4>
                        <div class="article-authors">
                            <strong>${ref.authors}</strong> &bull; <em>${ref.journal}</em> (${ref.year})
                            ${ref.doi ? `<span style="margin-left: 8px; font-family: var(--font-mono); font-size: 0.75rem;">DOI: ${ref.doi}</span>` : ''}
                        </div>
                        <p class="article-summary" style="margin-top: 8px; font-size: 0.85rem; line-height: 1.45;">
                            ${ref.summary}
                        </p>
                        ${ref.relevance_to_avatar ? `
                            <div class="avatar-relevance-box" style="margin-top: 8px; padding: 8px 12px; background: rgba(51, 65, 85, 0.06); border-left: 3px solid var(--accent-cyan); border-radius: var(--radius-sm); font-size: 0.78rem;">
                                <strong>RareAvatar Grounding:</strong> ${ref.relevance_to_avatar}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        } catch (e) {
            console.error('Failed to load literature:', e);
            container.innerHTML = `<div class="text-danger p-3">Error loading literature records: ${e.message}</div>`;
        }
    },

    async loadActivePatientProvenance() {
        const container = document.getElementById('active-patient-provenance-box');
        if (!container) return;

        if (!State.currentPatientId) {
            container.innerHTML = `
                <div class="empty-state-card text-center" style="padding: 30px;">
                    <p class="text-muted">Select or synthesize an active patient avatar to view PubMed evidence provenance.</p>
                </div>
            `;
            return;
        }

        try {
            const prov = await API.getPatientProvenance(State.currentPatientId);
            this.renderPatientProvenance(prov);
        } catch (e) {
            console.warn('Could not load patient provenance:', e);
            container.innerHTML = `<div class="text-muted p-3">Literature provenance unavailable for this avatar.</div>`;
        }
    },

    renderPatientProvenance(prov) {
        const container = document.getElementById('active-patient-provenance-box');
        if (!container) return;

        const patientIdEl = document.getElementById('provenance-patient-id');
        if (patientIdEl) patientIdEl.textContent = prov.patient_id;

        const diseaseEl = document.getElementById('provenance-disease-name');
        if (diseaseEl) diseaseEl.textContent = prov.disease_name;

        const stageEl = document.getElementById('provenance-stage');
        if (stageEl) stageEl.textContent = `Epistemic Confidence: ${(prov.epistemic_confidence_score * 100).toFixed(0)}%`;

        const findings = prov.findings_provenance || [];
        const symptoms = findings.filter(f => f.modality === 'SYMPTOM');
        const labs = findings.filter(f => f.modality === 'LABORATORY');
        const imaging = findings.filter(f => f.modality === 'IMAGING');
        const therapies = findings.filter(f => f.modality === 'TREATMENT');

        const renderSection = (title, items, icon) => {
            if (!items || items.length === 0) return '';
            return `
                <div class="provenance-section" style="margin-bottom: 20px;">
                    <h4 style="font-size: 0.95rem; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                        <span>${icon}</span> ${title} (${items.length})
                    </h4>
                    <div class="provenance-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
                        ${items.map(it => {
                            const p = it.provenance || {};
                            const pmids = p.literature_references || [];
                            return `
                                <div class="provenance-item-card card glass-card" style="padding: 12px; border-left: 3px solid var(--accent-cyan);">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <strong style="font-size: 0.88rem;">${it.feature_name}</strong>
                                        <span class="badge ${it.is_abnormal ? 'badge-danger' : 'badge-success'}">
                                            ${it.is_abnormal ? 'ABNORMAL' : 'GROUNDED'}
                                        </span>
                                    </div>
                                    <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--accent-cyan); margin-top: 4px;">
                                        Observed Value: ${it.observed_value}
                                    </div>
                                    <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 6px; line-height: 1.4;">
                                        ${p.clinical_significance || p.extract || ''}
                                    </div>
                                    <div style="display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px;">
                                        ${pmids.map(ref => `
                                            <a href="https://pubmed.ncbi.nlm.nih.gov/${ref.pmid}/" target="_blank" rel="noopener noreferrer" class="badge badge-mono pmid-link" style="font-size: 0.7rem;">
                                                PMID: ${ref.pmid}
                                            </a>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        };

        container.innerHTML = `
            ${renderSection('Cardinal Symptoms & Phenotypes', symptoms, '🩺')}
            ${renderSection('Pathophysiological Laboratory Biomarkers', labs, '🧪')}
            ${renderSection('Diagnostic Imaging Studies', imaging, '🔬')}
            ${renderSection('Grounded Therapeutic Interventions', therapies, '💊')}
        `;
    },

    async loadBiomarkerCatalog() {
        const tbody = document.getElementById('tbody-biomarker-catalog');
        if (!tbody) return;

        try {
            this.catalog = await API.getEvidenceCatalog();
            tbody.innerHTML = this.catalog.map(f => `
                <tr>
                    <td><strong>${f.finding_name}</strong><br><span style="font-size: 0.7rem; font-family: var(--font-mono); color: var(--text-muted);">${f.finding_key}</span></td>
                    <td><span class="badge badge-mono">${f.category}</span></td>
                    <td style="font-size: 0.8rem; line-height: 1.4;">${f.clinical_significance}</td>
                    <td>
                        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                            ${f.supporting_pmids.map(pmid => `
                                <a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" target="_blank" rel="noopener noreferrer" class="badge badge-mono pmid-link" style="font-size: 0.7rem;">
                                    ${pmid}
                                </a>
                            `).join('')}
                        </div>
                    </td>
                    <td style="font-size: 0.75rem; color: var(--text-secondary);">${f.guideline_source || '—'}</td>
                </tr>
            `).join('');
        } catch (e) {
            console.warn('Could not load biomarker catalog:', e);
            tbody.innerHTML = `<tr><td colspan="5" class="text-muted text-center">Biomarker catalog unavailable.</td></tr>`;
        }
    }
};
