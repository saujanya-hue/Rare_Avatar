const State = {
    currentUser: null,
    currentPatientId: null,
    currentPatientFull: null,
    currentTraineeView: null,
    isSupervisorMode: false,
    activeTab: 'workspace',
    currentTestCase: null,
    consultationMessages: [],

    listeners: [],

    subscribe(fn) {
        this.listeners.push(fn);
    },

    notify(event, data) {
        for (const fn of this.listeners) {
            try { fn(event, data); } catch (e) { console.error('State listener error:', e); }
        }
    },

    setUserSession(user) {
        this.currentUser = user;
        const isSupervisor = user.role === 'supervisor';
        this.setSupervisorMode(isSupervisor);
        try {
            localStorage.setItem('rareavatar_user', JSON.stringify(user));
        } catch (e) {}
        this.notify('userLoggedIn', user);
    },

    clearUserSession() {
        this.currentUser = null;
        try {
            localStorage.removeItem('rareavatar_user');
        } catch (e) {}
        this.setSupervisorMode(false);
        this.notify('userLoggedOut', null);
    },

    loadUserSession() {
        try {
            const raw = localStorage.getItem('rareavatar_user');
            if (raw) {
                const user = JSON.parse(raw);
                this.currentUser = user;
                this.setSupervisorMode(user.role === 'supervisor');
                return user;
            }
        } catch (e) {}
        return null;
    },

    setSupervisorMode(isSupervisor) {
        this.isSupervisorMode = isSupervisor;
        document.body.classList.toggle('supervisor-mode', isSupervisor);
        document.body.classList.toggle('trainee-mode', !isSupervisor);
        this.notify('modeChanged', isSupervisor);
    },

    async setPatient(patientId, isRefresh = false) {
        this.currentPatientId = patientId;
        try {
            const [full, trainee] = await Promise.all([
                API.getPatientFull(patientId),
                API.getTraineeView(patientId)
            ]);
            this.currentPatientFull = full;
            this.currentTraineeView = trainee;
            this.notify('patientLoaded', { full, trainee, isRefresh });
        } catch (e) {
            console.error('Failed to load patient state:', e);
            throw e;
        }
    },

    async refreshPatient() {
        if (!this.currentPatientId) return;
        await this.setPatient(this.currentPatientId, true);
    }
};
