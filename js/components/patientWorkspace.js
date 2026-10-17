/**
 * Patient Workspace Component
 */
const PatientWorkspace = {
    init() {
        State.subscribe((event, data) => {
            if (event === 'patientLoaded' || event === 'modeChanged') {
                this.render();
            }
        });

        // Time advance buttons
        document.getElementById('btn-advance-3m')?.addEventListener('click', () => this.advanceTime(3));
        document.getElementById('btn-advance-6m')?.addEventListener('click', () => this.advanceTime(6));
        document.getElementById('btn-advance-12m')?.addEventListener('click', () => this.advanceTime(12));
    },

    async advanceTime(months) {
        if (!State.currentPatientId) return;
        try {
            const res = await API.advanceTime(State.currentPatientId, months);
            App.showToast(`Simulation advanced by +${months} months to Month ${res.current_month}.`);
            await State.refreshPatient();
        } catch (e) {
            App.showToast(`Error: ${e.message}`);
        }
    },

    render() {
        const full = State.currentPatientFull;
        const trainee = State.currentTraineeView;
        if (!full || !trainee) return;

        const isSupervisor = State.isSupervisorMode;

        // Header and Demographic Profile
        document.getElementById('patient-id-badge').textContent = `ID: ${trainee.patient_id}`;
        document.getElementById('disp-age').textContent = `${trainee.age_years} years old`;
        document.getElementById('disp-sex').textContent = trainee.biological_sex;
        document.getElementById('disp-ethnicity').textContent = trainee.ethnicity;
        document.getElementById('disp-sim-month').textContent = `Month ${trainee.current_simulation_month}`;
        document.getElementById('simulation-clock-label').textContent = `Sim Month: ${trainee.current_simulation_month}`;

        // Ground truth fields
        const diseaseElem = document.getElementById('disp-disease-name');
        const omimElem = document.getElementById('disp-omim-code');

        if (isSupervisor) {
            diseaseElem.textContent = full.disease.disease_name;
            diseaseElem.classList.remove('highlight-cyan');
            diseaseElem.classList.add('highlight-purple');
            diseaseElem.title = full.disease.disease_name;
            omimElem.textContent = `${full.disease.omim_id} | ${full.disease.orpha_code}`;
            omimElem.title = `${full.disease.omim_id} | ${full.disease.orpha_code}`;
        } else {
            diseaseElem.textContent = 'Unlocked';
            diseaseElem.classList.add('highlight-purple');
            diseaseElem.title = full.disease ? full.disease.disease_name : 'Unlocked';
            omimElem.textContent = 'Unlocked';
            omimElem.title = full.disease ? `${full.disease.omim_id} | ${full.disease.orpha_code}` : 'Unlocked';
        }

        // Timeline Encounter Notes
        const notesContainer = document.getElementById('clinical-notes-timeline');
        const notes = isSupervisor ? full.clinical_notes : trainee.available_notes;

        if (notes && notes.length > 0) {
            notesContainer.innerHTML = notes.map(n => `
                <div class="timeline-event-card">
                    <div class="timeline-event-header">
                        <span class="timeline-month-badge">Month ${n.timestamp_month}</span>
                        <span class="timeline-encounter-type">${n.encounter_type}</span>
                    </div>
                    <div class="timeline-chief-complaint">${n.chief_complaint}</div>
                    <div class="timeline-narrative">${n.hpi}</div>
                </div>
            `).join('');
        } else {
            notesContainer.innerHTML = `<p class="text-muted" style="padding:16px;">No clinical encounters documented yet.</p>`;
        }

        // Symptoms Manifestations
        const symptomsList = document.getElementById('symptoms-display-list');
        const symptoms = full.symptoms;
        const revealedCount = symptoms.filter(s => s.is_revealed).length;
        document.getElementById('revealed-count-badge').textContent = `Revealed: ${revealedCount} / ${symptoms.length}`;

        symptomsList.innerHTML = symptoms.map(s => {
            const isRevealed = s.is_revealed || isSupervisor;
            const cardClass = isRevealed ? 'symptom-item-card' : 'symptom-item-card unrevealed';
            const nameDisplay = isRevealed ? s.name : 'Unreported Clinical Sign (Inquire to reveal)';
            const descDisplay = isRevealed ? s.description : 'Explore through clinician questioning to uncover this finding.';
            const onsetDisplay = isRevealed ? `Onset: Month ${s.onset_month}` : 'Onset: Hidden';
            const severityPercent = (s.severity_score / 10.0) * 100;

            return `
                <div class="${cardClass}">
                    <div class="symptom-item-top">
                        <span class="symptom-title">${nameDisplay}</span>
                        <span class="badge badge-mono">${onsetDisplay}</span>
                    </div>
                    <p class="symptom-desc">${descDisplay}</p>
                    ${isRevealed ? `
                        <div class="severity-meter" title="Severity Score: ${s.severity_score}/10">
                            <div class="severity-fill" style="width: ${severityPercent}%;"></div>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
};
