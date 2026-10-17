/**
 * Main Application Orchestrator
 */
const App = {
    async init() {
        this.setupThemeToggle();
        this.setupNavigation();
        this.setupSidebarToggle();
        this.setupModeToggle();
        this.setupAvatarModal();

        // Auth portal entry & session gate
        AuthPortal.init();

        // Initialize components
        PatientWorkspace.init();
        InteractiveConsultation.init();
        MultimodalViewer.init();
        ScenarioSimulation.init();
        await UncertaintyEvidence.init();
        ValidationPrivacy.init();
        StressTesting.init();
        await AdversarialArena.init();
        TraineeDiagnostics.init();
        await SupervisorOversight.init();
        await EvidenceExplorer.init();
        await WhatIfLab.init();
        await MysteryMode.init();
        await PopulationLab.init();

        // Load existing avatars
        await this.loadAvatars();
    },

    setupThemeToggle() {
        // Strictly enforce clinical white theme default
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        try {
            localStorage.removeItem('rareavatar_theme');
        } catch (_) {}
    },

    activateTab(target) {
        if (target === 'benchmark') target = 'arena';

        // Guard tabs based on user role if user logged in
        if (State.currentUser) {
            const isSupervisor = State.currentUser.role === 'supervisor';
            const supervisorOnlyTabs = ['arena', 'validation', 'uncertainty', 'supervisor-oversight', 'population'];
            if (!isSupervisor && supervisorOnlyTabs.includes(target)) {
                target = 'workspace';
            }
        }

        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(t => t.classList.toggle('active', t.getAttribute('data-tab') === target));

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${target}`));
        State.activeTab = target;

        if (target === 'multimodal') {
            MultimodalViewer.render();
        } else if (target === 'progression') {
            ScenarioSimulation.render();
        } else if (target === 'consultation') {
            InteractiveConsultation.renderChatForActivePatient();
        } else if (target === 'arena') {
            AdversarialArena.renderExperimentResults();
        } else if (target === 'trainee-submission') {
            TraineeDiagnostics.updateActivePatientInfo();
        } else if (target === 'supervisor-oversight') {
            SupervisorOversight.loadRecords();
        } else if (target === 'evidence') {
            EvidenceExplorer.render();
        } else if (target === 'what-if') {
            WhatIfLab.render();
        } else if (target === 'mystery') {
            MysteryMode.render();
        } else if (target === 'population') {
            PopulationLab.render();
        } else if (target === 'validation') {
            ValidationPrivacy.runAudit();
        }
    },


    setupNavigation() {
        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-tab');
                this.activateTab(target);
                window.location.hash = target;
            });
        });

        // Check hash on startup
        const hash = window.location.hash.replace('#', '');
        if (hash) {
            this.activateTab(hash);
        }

        window.addEventListener('hashchange', () => {
            const h = window.location.hash.replace('#', '');
            if (h) this.activateTab(h);
        });
    },

    setupSidebarToggle() {
        const btnToggle = document.getElementById('btn-toggle-sidebar');
        const sidebar = document.getElementById('app-sidebar');
        btnToggle?.addEventListener('click', () => {
            sidebar?.classList.toggle('collapsed');
            const isCollapsed = sidebar?.classList.contains('collapsed');
            btnToggle.textContent = isCollapsed ? '▶' : '◀';
            btnToggle.title = isCollapsed ? 'Expand Sidebar Menu' : 'Collapse Sidebar Menu';
            setTimeout(() => window.dispatchEvent(new Event('resize')), 220);
        });
    },

    setupModeToggle() {
        const btnTrainee = document.getElementById('btn-mode-trainee');
        const btnSupervisor = document.getElementById('btn-mode-supervisor');

        btnTrainee?.addEventListener('click', () => {
            btnTrainee.classList.add('active');
            btnSupervisor.classList.remove('active');
            State.setSupervisorMode(false);
            this.showToast('Switched to Trainee Mode (Blinded Diagnostic View)');
        });

        btnSupervisor?.addEventListener('click', () => {
            btnSupervisor.classList.add('active');
            btnTrainee.classList.remove('active');
            State.setSupervisorMode(true);
            this.showToast('Switched to Supervisor Mode (Full Ground Truth Unlocked)');
        });
    },

    setupAvatarModal() {
        const modal = document.getElementById('modal-create-avatar');
        const btnOpen = document.getElementById('btn-create-avatar-modal');
        const btnClose = document.getElementById('btn-close-create-modal');
        const btnCancel = document.getElementById('btn-cancel-create');
        const form = document.getElementById('form-create-avatar');

        const openModal = () => modal.classList.remove('hidden');
        const closeModal = () => modal.classList.add('hidden');

        btnOpen?.addEventListener('click', openModal);
        btnClose?.addEventListener('click', closeModal);
        btnCancel?.addEventListener('click', closeModal);

        // Click outside on modal overlay backdrop closes modal
        modal?.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Escape key closes modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });

        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const diseaseId = document.getElementById('select-new-disease').value;
            const ageVal = document.getElementById('input-new-age').value;
            const sexVal = document.getElementById('select-new-sex').value;
            const seedVal = document.getElementById('input-new-seed').value;

            try {
                const age = ageVal ? parseInt(ageVal) : null;
                const sex = sexVal || null;
                const seed = seedVal ? parseInt(seedVal) : null;

                const newPatient = await API.generatePatient(diseaseId, age, sex, seed);
                this.showToast(`Synthesized new avatar: ${newPatient.patient_id}`);
                closeModal();
                form.reset();

                await this.loadAvatars(newPatient.patient_id);
            } catch (err) {
                this.showToast(`Failed to synthesize avatar: ${err.message}`);
            }
        });
    },

    async loadAvatars(selectId = null) {
        try {
            const list = await API.listPatients();
            const dropdown = document.getElementById('select-patient');
            if (!dropdown) return;

            dropdown.innerHTML = list.map(p => `
                <option value="${p.patient_id}">
                    ${p.patient_id} — ${p.disease_name.split('(')[0]} (${p.age_years}yo ${p.biological_sex})
                </option>
            `).join('');

            dropdown.onchange = (e) => {
                State.setPatient(e.target.value);
            };

            const targetId = selectId || (list.length > 0 ? list[0].patient_id : null);
            if (targetId) {
                dropdown.value = targetId;
                await State.setPatient(targetId);
            }
        } catch (e) {
            console.error('Failed to load patient avatars list:', e);
            this.showToast('Error loading avatars from backend.');
        }
    },

    showToast(message) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 4000);
    }
};

window.addEventListener('DOMContentLoaded', () => {
    App.init();
});
