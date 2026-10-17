/**
 * Authentication & Portal Entry Gate Component
 * Handles Trainee (<id>@ggmail.com) and Supervisor login entries,
 * role validation, session switching, and dashboard gating.
 */
const AuthPortal = {
    activeRole: 'trainee',

    init() {
        this.bindEvents();
        this.checkExistingSession();
    },

    bindEvents() {
        // Tab switching in Login Portal (Trainee vs Supervisor)
        const tabTrainee = document.getElementById('login-tab-trainee');
        const tabSupervisor = document.getElementById('login-tab-supervisor');
        const formTrainee = document.getElementById('form-login-trainee');
        const formSupervisor = document.getElementById('form-login-supervisor');

        tabTrainee?.addEventListener('click', () => {
            this.activeRole = 'trainee';
            tabTrainee.classList.add('active');
            tabSupervisor?.classList.remove('active');
            formTrainee?.classList.remove('hidden');
            formSupervisor?.classList.add('hidden');
            this.clearErrors();
        });

        tabSupervisor?.addEventListener('click', () => {
            this.activeRole = 'supervisor';
            tabSupervisor.classList.add('active');
            tabTrainee?.classList.remove('active');
            formSupervisor?.classList.remove('hidden');
            formTrainee?.classList.add('hidden');
            this.clearErrors();
        });

        // 1-Click Demo Fill buttons
        document.getElementById('btn-demo-trainee-1')?.addEventListener('click', () => {
            const input = document.getElementById('input-trainee-email');
            if (input) input.value = 'TR-8041@ggmail.com';
            const pass = document.getElementById('input-trainee-password');
            if (pass) pass.value = 'trainee123';
        });

        document.getElementById('btn-demo-trainee-2')?.addEventListener('click', () => {
            const input = document.getElementById('input-trainee-email');
            if (input) input.value = 'TR-9042@ggmail.com';
            const pass = document.getElementById('input-trainee-password');
            if (pass) pass.value = 'trainee123';
        });

        document.getElementById('btn-demo-supervisor')?.addEventListener('click', () => {
            const input = document.getElementById('input-supervisor-email');
            if (input) input.value = 'SUP-001@ggmail.com';
            const pass = document.getElementById('input-supervisor-password');
            if (pass) pass.value = 'supervisor123';
        });

        // Trainee Form Submit
        formTrainee?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('input-trainee-email');
            const passwordInput = document.getElementById('input-trainee-password');
            const email = (emailInput?.value || '').trim();
            const password = passwordInput?.value || '';

            // Strict Trainee validation: must contain trainee ID and end in @ggmail.com
            if (!email.toLowerCase().endsWith('@ggmail.com')) {
                this.showError('Trainee login email must contain your Trainee ID ending in @ggmail.com (e.g., TR-8041@ggmail.com).');
                return;
            }

            const prefix = email.split('@')[0];
            if (!prefix || prefix.length < 2) {
                this.showError('Please enter a valid Trainee ID before @ggmail.com (e.g. TR-8041).');
                return;
            }

            try {
                this.setLoading(true);
                const resp = await API.login(email, password, 'trainee');
                this.onLoginSuccess(resp.user);
            } catch (err) {
                this.showError(err.message || 'Login failed.');
            } finally {
                this.setLoading(false);
            }
        });

        // Supervisor Form Submit
        formSupervisor?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('input-supervisor-email');
            const passwordInput = document.getElementById('input-supervisor-password');
            const email = (emailInput?.value || '').trim();
            const password = passwordInput?.value || '';

            if (!email || !email.includes('@')) {
                this.showError('Please enter a valid supervisor email (e.g., SUP-001@ggmail.com or supervisor@ggmail.com).');
                return;
            }

            try {
                this.setLoading(true);
                const resp = await API.login(email, password, 'supervisor');
                this.onLoginSuccess(resp.user);
            } catch (err) {
                this.showError(err.message || 'Supervisor authentication failed.');
            } finally {
                this.setLoading(false);
            }
        });

        // Header Logout button
        document.getElementById('btn-header-logout')?.addEventListener('click', () => {
            this.handleLogout();
        });
    },

    checkExistingSession() {
        const user = State.loadUserSession();
        if (user) {
            this.applyUserRoleToUI(user);
            this.showAppShell();
        } else {
            this.showLoginPortal();
        }
    },

    onLoginSuccess(user) {
        State.setUserSession(user);
        this.applyUserRoleToUI(user);
        this.showAppShell();
        App.showToast(`Logged in successfully as ${user.display_name}`);

        // If trainee, default to workspace tab; if supervisor, can view workspace or oversight
        App.activateTab('workspace');
    },

    handleLogout() {
        State.clearUserSession();
        this.showLoginPortal();
        App.showToast('You have been logged out of the clinical workstation.');
    },

    showLoginPortal() {
        document.getElementById('view-auth-portal')?.classList.remove('hidden');
        document.getElementById('view-app-shell')?.classList.add('hidden');
        this.clearErrors();
    },

    showAppShell() {
        document.getElementById('view-auth-portal')?.classList.add('hidden');
        document.getElementById('view-app-shell')?.classList.remove('hidden');
    },

    showError(msg) {
        const errBox = document.getElementById('login-error-alert');
        if (errBox) {
            errBox.textContent = msg;
            errBox.classList.remove('hidden');
        }
    },

    clearErrors() {
        const errBox = document.getElementById('login-error-alert');
        if (errBox) {
            errBox.textContent = '';
            errBox.classList.add('hidden');
        }
    },

    setLoading(loading) {
        const btns = document.querySelectorAll('.btn-login-submit');
        btns.forEach(b => {
            b.disabled = loading;
            if (loading) b.classList.add('loading');
            else b.classList.remove('loading');
        });
    },

    applyUserRoleToUI(user) {
        const isSupervisor = user.role === 'supervisor';
        const isTrainee = !isSupervisor;

        // Update body role classes
        document.body.classList.toggle('role-supervisor', isSupervisor);
        document.body.classList.toggle('role-trainee', isTrainee);

        // Update Header user badge
        const badgeElem = document.getElementById('header-user-badge');
        if (badgeElem) {
            badgeElem.className = isSupervisor ? 'badge badge-purple' : 'badge badge-cyan';
            badgeElem.innerHTML = isSupervisor
                ? `<span>🎓 Supervisor: <strong>${user.user_id}</strong></span>`
                : `<span>👤 Trainee: <strong>${user.user_id}</strong></span>`;
        }

        // Update Tab & Section Visibility in Left Sidebar
        document.querySelectorAll('[data-role]').forEach(el => {
            const roleReq = el.getAttribute('data-role');
            if (roleReq === 'trainee-only') {
                el.style.display = isTrainee ? 'flex' : 'none';
            } else if (roleReq === 'supervisor-only') {
                el.style.display = isSupervisor ? 'flex' : 'none';
            }
        });
        document.querySelectorAll('.nav-tab:not([data-role])').forEach(tab => {
            tab.style.display = 'flex';
        });

        // Update sidebar footer role status
        const sidebarRoleInd = document.getElementById('sidebar-role-indicator');
        if (sidebarRoleInd) {
            sidebarRoleInd.textContent = isSupervisor ? 'Supervisor Hub' : 'Trainee Clinic';
        }

        // Toggle avatar creation modal button (only supervisors can synthesize new random avatars)
        const btnCreateAvatar = document.getElementById('btn-create-avatar-modal');
        if (btnCreateAvatar) {
            btnCreateAvatar.style.display = isSupervisor ? 'inline-flex' : 'none';
        }

        // Re-render patient workspace according to role
        if (State.currentPatientId) {
            PatientWorkspace.render(State.isSupervisorMode ? State.currentPatientFull : State.currentTraineeView);
        }
    }
};
