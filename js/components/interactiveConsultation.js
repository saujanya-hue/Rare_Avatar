/**
 * Interactive Consultation Component
 * High-fidelity grounded dialogue with rare-disease patient avatars.
 */
const InteractiveConsultation = {
    chatHistories: {},
    isSubmitting: false,

    init() {
        this.loadHistoriesFromStorage();

        State.subscribe((event, data) => {
            if (event === 'patientLoaded') {
                this.renderChatForActivePatient();
                this.renderOrders();
            }
        });

        // Form submit handler
        const form = document.getElementById('form-consultation-chat');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleUserSubmit();
        });

        // Dedicated Button Click handler
        const sendBtn = document.getElementById('btn-send-query');
        sendBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleUserSubmit();
        });

        // Enter key in input field
        const input = document.getElementById('input-chat-query');
        input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.handleUserSubmit();
            }
        });

        // Quick Inquiry Chips
        document.querySelectorAll('.chip-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const query = btn.getAttribute('data-query');
                const chatInput = document.getElementById('input-chat-query');
                if (chatInput && query) {
                    chatInput.value = query;
                    this.handleUserSubmit();
                }
            });
        });
    },

    loadHistoriesFromStorage() {
        try {
            const saved = sessionStorage.getItem('rareavatar_chat_histories');
            if (saved) {
                this.chatHistories = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('Unable to load chat histories from storage:', e);
        }
    },

    saveHistoriesToStorage() {
        try {
            sessionStorage.setItem('rareavatar_chat_histories', JSON.stringify(this.chatHistories));
        } catch (e) {
            console.warn('Unable to save chat histories to storage:', e);
        }
    },

    getActivePatientId() {
        if (State.currentPatientId) return State.currentPatientId;
        const dropdown = document.getElementById('select-patient');
        if (dropdown && dropdown.value) return dropdown.value;
        if (State.currentPatientFull && State.currentPatientFull.patient_id) return State.currentPatientFull.patient_id;
        return 'default_patient';
    },

    getMessagesForActivePatient() {
        const pid = this.getActivePatientId();
        if (!this.chatHistories[pid] || this.chatHistories[pid].length === 0) {
            this.chatHistories[pid] = [
                {
                    sender: 'avatar',
                    text: "Hello Doctor, thank you for seeing me. I've been feeling progressively unwell for several months, and nobody has been able to tell me what's wrong.",
                    entities: ['Chief Complaint'],
                    uncertainty: null,
                    citations: []
                }
            ];
            this.saveHistoriesToStorage();
        }
        return this.chatHistories[pid];
    },

    renderChatForActivePatient() {
        const messages = this.getMessagesForActivePatient();
        this.renderMessages(messages);
    },

    async handleUserSubmit() {
        if (this.isSubmitting) return;

        const input = document.getElementById('input-chat-query');
        if (!input) return;

        const queryText = input.value.trim();
        if (!queryText) return;

        const pid = this.getActivePatientId();
        if (!pid || pid === 'default_patient') {
            App.showToast('Please wait for the patient avatar to load.');
            return;
        }

        // Lock submission and clear input immediately
        this.isSubmitting = true;
        input.value = '';

        // Add clinician message to conversation
        const messages = this.getMessagesForActivePatient();
        messages.push({
            sender: 'clinician',
            text: queryText
        });
        this.renderMessages(messages);
        this.saveHistoriesToStorage();

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const resp = await API.sendInquiry(pid, queryText);
            this.removeTypingIndicator();

            messages.push({
                sender: 'avatar',
                text: resp.avatar_response,
                entities: resp.clinical_entities_identified || [],
                uncertainty: resp.uncertainty_statement || null,
                citations: resp.evidence_citations || []
            });
            this.renderMessages(messages);
            this.saveHistoriesToStorage();

            // Update revealed findings in active state without wiping consultation history
            if (resp.revealed_findings && resp.revealed_findings.length > 0 && State.currentPatientFull && State.currentPatientFull.symptoms) {
                for (const sym of State.currentPatientFull.symptoms) {
                    if (resp.revealed_findings.includes(sym.name)) {
                        sym.is_revealed = true;
                    }
                }
                PatientWorkspace.render();
            }
        } catch (e) {
            console.error('Inquiry error:', e);
            this.removeTypingIndicator();
            messages.push({
                sender: 'avatar',
                text: `[Clinical Inquiry Error: ${e.message}]`
            });
            this.renderMessages(messages);
            this.saveHistoriesToStorage();
        } finally {
            this.isSubmitting = false;
            // Refocus input field for seamless typing experience
            setTimeout(() => {
                input.focus();
            }, 100);
        }
    },

    showTypingIndicator() {
        const box = document.getElementById('chat-messages-box');
        if (!box) return;
        this.removeTypingIndicator();

        const indicator = document.createElement('div');
        indicator.id = 'chat-typing-indicator';
        indicator.className = 'chat-bubble avatar typing-bubble';
        indicator.innerHTML = `
            <div class="bubble-sender">Patient Avatar</div>
            <div class="bubble-text" style="display:flex; align-items:center; gap:8px; color:var(--text-secondary); font-style:italic;">
                <span>Reflecting on symptoms & formulating response...</span>
                <span class="loading-spinner-sm"></span>
            </div>
        `;
        box.appendChild(indicator);
        box.scrollTop = box.scrollHeight;
    },

    removeTypingIndicator() {
        const indicator = document.getElementById('chat-typing-indicator');
        if (indicator) indicator.remove();
    },

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    renderMessages(messages) {
        const box = document.getElementById('chat-messages-box');
        if (!box) return;
        const msgs = messages || this.getMessagesForActivePatient();

        box.innerHTML = msgs.map(m => {
            const isClinician = m.sender === 'clinician';
            return `
                <div class="chat-bubble ${isClinician ? 'clinician' : 'avatar'}">
                    <div class="bubble-sender">${isClinician ? 'Dr. Trainee / Clinician' : 'Patient Avatar'}</div>
                    <div class="bubble-text">${this.escapeHtml(m.text)}</div>
                </div>
            `;
        }).join('');

        box.scrollTop = box.scrollHeight;
    },

    renderOrders() {
        const catalogBox = document.getElementById('order-catalog-box');
        const trainee = State.currentTraineeView;
        if (!catalogBox || !trainee) return;

        const catalog = trainee.available_test_catalog;
        if (!catalog || catalog.length === 0) {
            catalogBox.innerHTML = `<p class="text-muted" style="font-size:0.8rem; padding:12px;">All available diagnostic tests have been performed and reported.</p>`;
            return;
        }

        catalogBox.innerHTML = catalog.map(item => `
            <div class="order-item-card">
                <div class="order-item-info">
                    <span class="order-item-title">${this.escapeHtml(item.name)}</span>
                    <span class="order-item-sub">${this.escapeHtml(item.category)} (${this.escapeHtml(item.type.toUpperCase())})</span>
                </div>
                <button type="button" class="btn btn-sm btn-outline-cyan btn-place-order" 
                        data-type="${this.escapeHtml(item.type)}" 
                        data-code="${this.escapeHtml(item.code)}">
                    Order
                </button>
            </div>
        `).join('');

        // Bind order buttons
        catalogBox.querySelectorAll('.btn-place-order').forEach(btn => {
            btn.addEventListener('click', async () => {
                const type = btn.getAttribute('data-type');
                const code = btn.getAttribute('data-code');
                try {
                    btn.disabled = true;
                    btn.textContent = 'Ordering...';
                    const res = await API.orderInvestigation(State.currentPatientId, type, code);
                    App.showToast(res.message);
                    await State.refreshPatient();
                } catch (e) {
                    App.showToast(`Order failed: ${e.message}`);
                    btn.disabled = false;
                    btn.textContent = 'Order';
                }
            });
        });
    }
};
