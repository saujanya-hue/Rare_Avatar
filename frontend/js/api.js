/**
 * API Client for RareAvatar Backend
 */
const API = {
    async listPatients() {
        const res = await fetch('/api/patients');
        if (!res.ok) throw new Error('Failed to fetch patients');
        return await res.json();
    },

    async getPatientFull(patientId) {
        const res = await fetch(`/api/patients/${patientId}`);
        if (!res.ok) throw new Error(`Failed to fetch patient ${patientId}`);
        return await res.json();
    },

    async getTraineeView(patientId) {
        const res = await fetch(`/api/patients/${patientId}/trainee-view`);
        if (!res.ok) throw new Error(`Failed to fetch trainee view for ${patientId}`);
        return await res.json();
    },

    async generatePatient(diseaseId, age, sex, seed) {
        const params = new URLSearchParams({ disease_id: diseaseId });
        if (age) params.append('age_years', age);
        if (sex) params.append('biological_sex', sex);
        if (seed) params.append('seed', seed);
        const res = await fetch(`/api/patients/generate?${params.toString()}`, { method: 'POST' });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to generate patient');
        }
        return await res.json();
    },

    async sendInquiry(patientId, queryText) {
        const res = await fetch('/api/simulation/inquiry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, query_text: queryText })
        });
        if (!res.ok) throw new Error('Failed to send consultation inquiry');
        return await res.json();
    },

    async orderInvestigation(patientId, invType, codeOrId) {
        const res = await fetch('/api/simulation/order-investigation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                investigation_type: invType,
                test_code_or_study_id: codeOrId
            })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to order investigation');
        }
        return await res.json();
    },

    async advanceTime(patientId, months = 3) {
        const res = await fetch('/api/simulation/advance-time', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, advance_months: months })
        });
        if (!res.ok) throw new Error('Failed to advance simulation time');
        return await res.json();
    },

    async applyTreatment(patientId, scenarioId) {
        const res = await fetch('/api/simulation/apply-treatment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, scenario_id: scenarioId })
        });
        if (!res.ok) throw new Error('Failed to apply treatment scenario');
        return await res.json();
    },

    async getValidationAudit(patientId) {
        const res = await fetch(`/api/validation/audit/${patientId}`);
        if (!res.ok) throw new Error(`Failed to audit patient ${patientId}`);
        return await res.json();
    },

    async createTestCase(patientId, noiseSigma, missingRate, ageShift, injectInfection, seed) {
        const params = new URLSearchParams({
            patient_id: patientId,
            noise_sigma: noiseSigma,
            missing_lab_rate: missingRate,
            atypical_age_shift_years: ageShift,
            inject_confounding_infection: injectInfection,
            seed: seed
        });
        const res = await fetch(`/api/diagnostic-eval/create-test-case?${params.toString()}`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to create test case');
        return await res.json();
    },

    async evaluateBaseline(testCaseId) {
        const res = await fetch(`/api/diagnostic-eval/evaluate-baseline?test_case_id=${testCaseId}`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to evaluate baseline classifier');
        return await res.json();
    },

    async getBenchmarkHistory() {
        const res = await fetch('/api/diagnostic-eval/history');
        if (!res.ok) return [];
        return await res.json();
    },

    async listEvidence() {
        const res = await fetch('/api/evidence/list');
        if (!res.ok) return [];
        return await res.json();
    },

    async searchEvidence(query) {
        const res = await fetch(`/api/evidence/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) return [];
        return await res.json();
    },

    // ========================================================================
    // DIAGNOSTIC AI ADVERSARIAL ARENA APIS
    // ========================================================================
    async getArenaCapabilities() {
        const res = await fetch('/api/diagnostic-arena/capabilities');
        if (!res.ok) throw new Error('Failed to fetch arena capabilities');
        return await res.json();
    },

    async runArenaExperiment(config) {
        const res = await fetch('/api/diagnostic-arena/experiments/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Adversarial experiment failed');
        }
        return await res.json();
    },

    async listArenaExperiments() {
        const res = await fetch('/api/diagnostic-arena/experiments');
        if (!res.ok) return [];
        return await res.json();
    },

    async getArenaExperiment(experimentId) {
        const res = await fetch(`/api/diagnostic-arena/experiments/${experimentId}`);
        if (!res.ok) throw new Error(`Experiment ${experimentId} not found`);
        return await res.json();
    },

    async getArenaCase(caseId) {
        const res = await fetch(`/api/diagnostic-arena/cases/${caseId}`);
        if (!res.ok) throw new Error(`Case ${caseId} not found`);
        return await res.json();
    },

    // Authentication & Trainee Diagnostics
    async login(email, password = '', role = null) {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, role })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        return await res.json();
    },

    async submitTraineeDiagnosis(submission) {
        const res = await fetch('/api/auth/trainee-submit-diagnosis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submission)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to submit trainee diagnosis');
        }
        return await res.json();
    },

    async getSupervisorTraineeRecords() {
        const res = await fetch('/api/auth/supervisor/trainee-records');
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to fetch trainee oversight records');
        }
        return await res.json();
    },

    // Diagnostic AI Breaking Point Finder
    async searchBreakingPoint(config) {
        const res = await fetch('/api/diagnostic-arena/breaking-point/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Breaking point search failed');
        }
        return await res.json();
    },

    async compareBreakingPoint(config) {
        const res = await fetch('/api/diagnostic-arena/breaking-point/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Breaking point comparison failed');
        }
        return await res.json();
    },

    // ========================================================================
    // CLINICAL CONSISTENCY GUARDIAN APIS
    // ========================================================================
    async validateCase(patientSpec) {
        const res = await fetch('/api/validation/validate-case', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(patientSpec)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Validation failed');
        }
        return await res.json();
    },

    // ========================================================================
    // EVIDENCE EXPLORER APIS
    // ========================================================================
    async getEvidenceCatalog() {
        const res = await fetch('/api/evidence/catalog');
        if (!res.ok) return [];
        return await res.json();
    },

    async getEvidenceSummary() {
        const res = await fetch('/api/evidence/summary');
        if (!res.ok) throw new Error('Failed to fetch evidence summary');
        return await res.json();
    },

    async getEvidenceByDisease(diseaseId) {
        const res = await fetch(`/api/evidence/by-disease/${diseaseId}`);
        if (!res.ok) return [];
        return await res.json();
    },

    async getPatientProvenance(patientId) {
        const res = await fetch(`/api/evidence/provenance/${patientId}`);
        if (!res.ok) throw new Error(`Evidence provenance for ${patientId} not found`);
        return await res.json();
    },

    async getFindingProvenance(findingKey, diseaseId = null) {
        const url = diseaseId 
            ? `/api/evidence/finding/${findingKey}?disease_id=${diseaseId}`
            : `/api/evidence/finding/${findingKey}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Finding provenance for ${findingKey} not found`);
        return await res.json();
    },

    // ========================================================================
    // CLINICAL WHAT-IF LAB APIS
    // ========================================================================
    async createWhatIfBranch(config) {
        const res = await fetch('/api/what-if/branches/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to create simulation branch');
        }
        return await res.json();
    },

    async listPatientBranches(patientId) {
        const res = await fetch(`/api/what-if/branches/patient/${patientId}`);
        if (!res.ok) return [];
        return await res.json();
    },

    async getBranchDetails(branchId) {
        const res = await fetch(`/api/what-if/branches/${branchId}`);
        if (!res.ok) throw new Error(`Branch ${branchId} not found`);
        return await res.json();
    },

    async advanceWhatIfBranch(branchId, advanceMonths = 3) {
        const res = await fetch('/api/what-if/branches/advance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branch_id: branchId, advance_months: advanceMonths })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to advance branch');
        }
        return await res.json();
    },

    async compareWhatIfBranches(patientId, branchIds = []) {
        const res = await fetch('/api/what-if/branches/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: patientId, branch_ids: branchIds })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to compare branches');
        }
        return await res.json();
    },

    // ========================================================================
    // CLINICAL MYSTERY MODE APIS
    // ========================================================================
    async startMysterySession(config) {
        const res = await fetch('/api/mystery/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to start mystery session');
        }
        return await res.json();
    },

    async getMysterySession(sessionId) {
        const res = await fetch(`/api/mystery/session/${sessionId}`);
        if (!res.ok) throw new Error(`Mystery session ${sessionId} not found`);
        return await res.json();
    },

    async sendMysteryInquiry(sessionId, queryText) {
        const res = await fetch('/api/mystery/inquire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, query_text: queryText })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Mystery inquiry failed');
        }
        return await res.json();
    },

    async orderMysteryInvestigation(sessionId, investigationType, investigationCode) {
        const res = await fetch('/api/mystery/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                investigation_type: investigationType,
                code_or_acronym: investigationCode
            })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Investigation order failed');
        }
        return await res.json();
    },

    async submitMysteryDiagnosis(submission) {
        const res = await fetch('/api/mystery/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submission)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Diagnosis submission failed');
        }
        return await res.json();
    },

    async getSupervisorMysterySessions() {
        const res = await fetch('/api/mystery/supervisor/sessions');
        if (!res.ok) return [];
        return await res.json();
    },

    async getInvestigationPricingCatalog() {
        const res = await fetch('/api/mystery/catalog/pricing');
        if (!res.ok) return [];
        return await res.json();
    },

    // ========================================================================
    // SYNTHETIC PATIENT POPULATION LAB APIS
    // ========================================================================
    async generatePopulationCohort(config) {
        const res = await fetch('/api/populations/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Cohort generation failed');
        }
        return await res.json();
    },

    async listPopulationCohorts() {
        const res = await fetch('/api/populations/cohorts');
        if (!res.ok) return [];
        return await res.json();
    },

    async getPopulationCohort(cohortId) {
        const res = await fetch(`/api/populations/cohorts/${cohortId}`);
        if (!res.ok) throw new Error(`Cohort ${cohortId} not found`);
        return await res.json();
    }
};

