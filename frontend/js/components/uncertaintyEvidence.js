/**
 * Uncertainty and Evidence Component
 */
const UncertaintyEvidence = {
    allEvidence: [],

    async init() {
        State.subscribe((event, data) => {
            if (event === 'patientLoaded') {
                this.renderUncertainty();
            }
        });

        // Search bar
        const searchInput = document.getElementById('input-lit-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterEvidence(e.target.value.trim());
        });

        try {
            this.allEvidence = await API.listEvidence();
            this.renderEvidence(this.allEvidence);
        } catch (e) {
            console.error('Failed to load evidence base:', e);
        }
    },

    renderUncertainty() {
        const full = State.currentPatientFull;
        if (!full) return;

        const container = document.getElementById('uncertainty-scores-list');
        if (!container) return;

        const labs = full.lab_history;
        container.innerHTML = labs.map(lab => {
            const unc = lab.uncertainty;
            const epistemicPercent = Math.round(unc.epistemic_confidence_score * 100);

            return `
                <div class="score-item">
                    <div>
                        <strong>${lab.test_name}</strong>
                        <div style="font-size:0.75rem; color:#94a3b8; margin-top:2px;">
                            ${unc.uncertainty_source}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span class="badge badge-cyan">Epistemic Confidence: ${epistemicPercent}%</span>
                        <div style="font-size:0.72rem; color:#f59e0b; margin-top:2px; font-family:var(--font-mono);">
                            Aleatoric σ²: ${unc.aleatoric_variance.toFixed(2)} | 95% CI: [${unc.ci_95_low}, ${unc.ci_95_high}]
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderEvidence(articles) {
        const container = document.getElementById('literature-articles-box');
        if (!container) return;

        if (articles.length === 0) {
            container.innerHTML = `<p class="text-muted" style="padding:16px;">No matching biomedical literature records found.</p>`;
            return;
        }

        container.innerHTML = articles.map(art => `
            <div class="article-card">
                <div class="article-top">
                    <span class="article-title">${art.title}</span>
                    <span class="badge badge-success">${art.evidence_level}</span>
                </div>
                <div class="article-authors">${art.authors} — <em>${art.journal} (${art.year})</em></div>
                <p class="article-summary">${art.relevance_summary}</p>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px; font-size:0.75rem;">
                    <span style="font-family:var(--font-mono); color:var(--accent-cyan);">PMID: ${art.pmid || 'N/A'} | DOI: ${art.doi || 'N/A'}</span>
                    ${art.url ? `<a href="${art.url}" target="_blank" rel="noopener noreferrer" style="color:var(--accent-cyan); text-decoration:none;">View on PubMed ↗</a>` : ''}
                </div>
            </div>
        `).join('');
    },

    filterEvidence(query) {
        if (!query) {
            this.renderEvidence(this.allEvidence);
            return;
        }
        const q = query.toLowerCase();
        const filtered = this.allEvidence.filter(a => 
            a.title.toLowerCase().includes(q) ||
            a.relevance_summary.toLowerCase().includes(q) ||
            a.authors.toLowerCase().includes(q) ||
            (a.pmid && a.pmid.includes(q))
        );
        this.renderEvidence(filtered);
    }
};
