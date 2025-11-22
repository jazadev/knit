window.civicApp = function () {
    return {
        darkMode: localStorage.getItem('theme') === 'dark',
        zoomLevel: parseInt(localStorage.getItem('zoomLevel')) || 100,
        lang: localStorage.getItem('lang') || 'es',
        isLoggedIn: !!window.SERVER_USER,
        mobileMenuOpen: false,
        t: window.CIVIC_DATA || {},

        // Modales
        showSettingsModal: false,
        showPrivacyModal: false,
        confirmModal: { show: false, message: '', callback: () => { } },

        // Auxiliares
        availableStates: [],
        errors: {},
        toast: { show: false, message: '', type: 'success' },
        userProfile: {
            name: window.SERVER_USER?.dbProfile?.name || window.SERVER_USER?.name || '',
            email: window.SERVER_USER?.dbProfile?.email || window.SERVER_USER?.preferred_username || '',
            age: window.SERVER_USER?.dbProfile?.age || '',
            gender: window.SERVER_USER?.dbProfile?.gender || '',
            platformLang: window.SERVER_USER?.dbProfile?.platformLang || 'es',
            country: window.SERVER_USER?.dbProfile?.country || '',
            state: window.SERVER_USER?.dbProfile?.state || '',
            phone: window.SERVER_USER?.dbProfile?.phone || '',
            channels: window.SERVER_USER?.dbPreferences?.notifications || { email: false, sms: false },
            topics: window.SERVER_USER?.dbTopics || JSON.parse(JSON.stringify(DEFAULT_TOPICS))
        },
        // variables para speech-to-text y text-to-speech
        isRecording: false,
        isSpeaking: false,
        currentSpeakingText: null,
        synthesizer: null,
        player: null,
        isPreparingRecording: false,

        showToastMessage(msg, type = 'success') {
            this.toast = { show: true, message: msg, type: type };
            setTimeout(() => { this.toast.show = false; }, 3000);
        },

        askConfirm(msgKey, callback) {
            this.confirmModal.message = this.t[this.lang][msgKey];
            this.confirmModal.callback = callback;
            this.confirmModal.show = true;
        },

        updateLocationLogic() {
            if (this.userProfile.country === 'MX') { this.availableStates = [{ code: 'CDMX', label: 'Ciudad de México' }]; }
            else if (this.userProfile.country === 'GT') { this.availableStates = [{ code: 'GUATE', label: 'Ciudad de Guatemala' }]; }
            else { this.availableStates = []; }

            if (this.userProfile.country && this.availableStates.length > 0) {
                const isValid = this.availableStates.some(s => s.code === this.userProfile.state);
                if (!isValid) this.userProfile.state = this.availableStates[0].code;
            } else if (!this.userProfile.country) {
                this.userProfile.state = '';
            }
        },

        toggleTopic(key) { let isEnabled = this.userProfile.topics[key].enabled; let subs = this.userProfile.topics[key].subs; for (let subKey in subs) { subs[subKey] = isEnabled; } },
        checkParent(topicKey) { this.userProfile.topics[topicKey].enabled = true; },

        // validación del formulario
        validateForm() {
            this.errors = {};
            let isValid = true;

            if (!this.userProfile.name.trim()) {
                this.errors.name = 'Requerido'; isValid = false;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!this.userProfile.email.trim() || !emailRegex.test(this.userProfile.email)) {
                this.errors.email = 'Correo inválido'; isValid = false;
            }

            if (this.userProfile.channels.sms) {
                const maxLen = this.userProfile.country === 'MX' ? 10 : 8;
                const currentLen = this.userProfile.phone ? this.userProfile.phone.length : 0;
                if (currentLen === 0) {
                    this.errors.phone = 'Requerido'; isValid = false;
                } else if (currentLen !== maxLen) {
                    this.errors.phone = `Debe ser de ${maxLen} dígitos`; isValid = false;
                }
            }
            return isValid;
        },

        async saveProfile() {
            if (!this.validateForm()) {
                this.showToastMessage('Revisa los errores marcados en rojo', 'error');
                return;
            }

            try {
                const res = await fetch('/api/save-profile', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.userProfile)
                });

                if (res.ok) {
                    this.showToastMessage('✅ Guardado correctamente');
                    this.errors = {};
                } else {
                    this.showToastMessage('❌ Error al guardar', 'error');
                }
            } catch (e) {
                console.error(e);
                this.showToastMessage('⚠️ Error de conexión', 'error');
            }
        },

        async deleteAccount(inputText) {
            const requiredWord = this.t[this.lang].keyword_delete;

            if (inputText && inputText.trim().toLowerCase() === requiredWord.toLowerCase()) {
                try {
                    // Llamar al backend para borrar de Cosmos DB
                    const res = await fetch('/api/delete-account', { method: 'POST' });

                    if (res.ok) {
                        this.showToastMessage(this.t[this.lang].msg_goodbye);

                        this.showSettingsModal = false;

                        setTimeout(() => {
                            this.logout();
                        }, 2500);

                    } else {
                        this.showToastMessage('Error al eliminar cuenta', 'error');
                    }
                } catch (e) {
                    console.error(e);
                    this.showToastMessage('Error de conexión', 'error');
                }
            } else {
                this.showToastMessage('Palabra de confirmación incorrecta', 'error');
            }
        },
        // Speech-to-Text
        async startRecording() {
            // Evitar doble clic o que se dispare mientras se prepara/graba
            if (this.isRecording || this.isPreparingRecording) return;

            this.isPreparingRecording = true;

            try {
                // obtener token efímero del backend
                const tokenRes = await fetch('/api/speech-token');
                const tokenData = await tokenRes.json();
                if (tokenData.error) throw new Error(tokenData.error);

                const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(
                    tokenData.token,
                    tokenData.region
                );

                // reconocer idioma según perfil usuario
                let recogLang = 'es-MX';
                if (this.userProfile.platformLang === 'en') {
                    recogLang = 'en-US';
                } else {
                    recogLang = this.userProfile.country === 'MX' ? 'es-MX' : 'es-ES';
                }
                speechConfig.speechRecognitionLanguage = recogLang;

                const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
                const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

                // delay antes de iniciar reconocimiento para que usuario vea animación
                setTimeout(() => {
                    this.isPreparingRecording = false;
                    this.isRecording = true;

                    recognizer.recognizeOnceAsync(
                        result => {
                            this.isRecording = false;

                            if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                                console.log('Texto reconocido crudo:', result.text);
                                const newText = (result.text || '').trim();

                                if (newText) {
                                    const current = this.$refs.inputMsg.value || '';
                                    this.$refs.inputMsg.value = (current ? current + ' ' : '') + newText;
                                    this.$refs.inputMsg.focus();
                                }
                            } else {
                                this.showToastMessage('No te escuché bien', 'error');
                            }

                            recognizer.close();
                        },
                        err => {
                            this.isRecording = false;
                            console.error(err);
                            this.showToastMessage('Error de micrófono', 'error');
                            recognizer.close();
                        }
                    );
                }, 300); // el usuario ve la animación y luego ya puede hablar, mejora el reconocimiento

            } catch (e) {
                console.error(e);
                this.isPreparingRecording = false;
                this.isRecording = false;
                this.showToastMessage('Error iniciando voz', 'error');
            }
        },


        // Text-to-Speech
        async speakText(text) {
            // Normalizamos texto para usarlo como ID del mensaje
            const cleanText = text.replace(/<[^>]*>?/gm, '').trim();

            // valida si es el mismo texto que ya está sonando
            const isSame = (this.currentSpeakingText === cleanText);

            // Si es el mismo y está sonando un STOP manual
            if (isSame && this.player) {
                try { this.player.pause(); } catch (e) { console.error(e); }
                this.player = null;

                if (this.synthesizer) {
                    this.synthesizer.close();
                    this.synthesizer = null;
                }

                this.isSpeaking = false;
                this.currentSpeakingText = null;
                return;
            }

            // Si había otro audio sonando lo detenemos antes de iniciar uno nuevo
            if (this.player) {
                try { this.player.pause(); } catch (e) { console.error(e); }
                this.player = null;
            }
            if (this.synthesizer) {
                this.synthesizer.close();
                this.synthesizer = null;
            }
            this.isSpeaking = false;
            this.currentSpeakingText = null;

            // nuevo audio
            try {
                this.currentSpeakingText = cleanText;
                this.isSpeaking = true;

                const tokenRes = await fetch('/api/speech-token');
                const tokenData = await tokenRes.json();

                const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(
                    tokenData.token,
                    tokenData.region
                );

                if (this.userProfile.platformLang === 'en') {
                    speechConfig.speechSynthesisVoiceName = 'en-US-AvaNeural';
                } else {
                    speechConfig.speechSynthesisVoiceName = 'es-MX-DaliaNeural';
                }

                this.player = new SpeechSDK.SpeakerAudioDestination();

                this.player.onAudioEnd = () => {
                    if (this.currentSpeakingText === cleanText) {
                        this.isSpeaking = false;
                        this.currentSpeakingText = null;

                        if (this.synthesizer) {
                            this.synthesizer.close();
                            this.synthesizer = null;
                        }
                        this.player = null;
                    }
                };

                const audioConfig = SpeechSDK.AudioConfig.fromSpeakerOutput(this.player);
                this.synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig, audioConfig);

                this.synthesizer.speakTextAsync(
                    cleanText,
                    result => {
                        // Si se canceló desde la SDK, limpiamos estado
                        if (result.reason === SpeechSDK.ResultReason.Canceled) {
                            if (this.currentSpeakingText === cleanText) {
                                this.isSpeaking = false;
                                this.currentSpeakingText = null;
                                this.player = null;
                            }
                        }
                    },
                    err => {
                        console.error(err);
                        if (this.currentSpeakingText === cleanText) {
                            this.isSpeaking = false;
                            this.currentSpeakingText = null;
                        }
                        if (this.synthesizer) {
                            this.synthesizer.close();
                            this.synthesizer = null;
                        }
                        this.player = null;
                        this.showToastMessage('Error de audio', 'error');
                    }
                );
            } catch (e) {
                console.error(e);
                this.showToastMessage('Error de audio', 'error');
                this.isSpeaking = false;
                this.currentSpeakingText = null;
                if (this.synthesizer) {
                    this.synthesizer.close();
                    this.synthesizer = null;
                }
                this.player = null;
            }
        },


        notificationsOpen: false,
        showNotificationsModal: false,
        notifications: [{ id: 1, text: 'Bienvenido...', time: 'Hace 5 min', read: false }],
        get hasUnread() { return this.notifications.some(n => !n.read); },

        chats: [],
        activeChatId: null,
        loading: false,

        async initChat() {
            // Usuario- cargar de API
            if (this.isLoggedIn) {
                try {
                    const res = await fetch('/api/chats');
                    if (res.ok) {
                        this.chats = await res.json();
                        this.chats = this.chats.map(c => ({ ...c, messages: c.messages || [] }));
                    }
                } catch (e) { console.error(e); }
            }
            // Invitado - cargar de LocalStorage
            else {
                try {
                    const stored = JSON.parse(localStorage.getItem('civic_chats'));
                    this.chats = Array.isArray(stored) ? stored : [];
                } catch (e) { this.chats = []; }
            }

            if (this.chats.length > 0) { this.activeChatId = this.chats[0].id; } else { this.activeChatId = null; }

            if (!this.isLoggedIn) {
                this.$watch('chats', val => localStorage.setItem('civic_chats', JSON.stringify(val)));
            }
        },
        createNewChat() { this.activeChatId = null; this.mobileMenuOpen = false; },

        async deleteChat(id, event) {
            if (event) event.stopPropagation();

            this.askConfirm('msg_confirm_delete_chat', async () => {
                if (this.isLoggedIn) {
                    try {
                        const res = await fetch(`/api/chats/${id}`, { method: 'DELETE' });
                        if (!res.ok) throw new Error('Error deleting');
                    } catch (e) {
                        this.showToastMessage('Error al borrar chat', 'error');
                        return;
                    }
                }
                this.chats = this.chats.filter(c => c.id !== id);
                if (this.activeChatId === id) this.activeChatId = this.chats.length > 0 ? this.chats[0].id : null;
            });
        },

        async clearAllChats() {
            if (this.chats.length === 0) return;

            this.askConfirm('msg_confirm_delete_all', async () => {
                if (this.isLoggedIn) {
                    try {
                        const res = await fetch('/api/chats', { method: 'DELETE' });
                        if (!res.ok) throw new Error('Error deleting all');
                        this.showToastMessage('Historial eliminado');
                    } catch (e) {
                        this.showToastMessage('Error al borrar historial', 'error');
                        return;
                    }
                }
                this.chats = [];
                this.activeChatId = null;
                this.mobileMenuOpen = false;
            });
        },

        get currentChat() {
            if (!this.activeChatId) return { messages: [] };
            return this.chats.find(c => c.id === this.activeChatId) || { messages: [] };
        },

        async sendMessage(text) {
            if (!text || !text.trim()) return;
            let chat = this.chats.find(c => c.id === this.activeChatId);
            if (!chat) {
                const newId = this.isLoggedIn ? 'chat_' + Date.now() : Date.now();
                chat = { id: newId, title: text.substring(0, 30) + '...', messages: [] };
                this.chats.unshift(chat);
                this.activeChatId = newId;
            }

            chat.messages.push({ role: 'user', text: text });
            this.loading = true;
            this.scrollToBottom();

            try {
                const res = await fetch('/chat', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, chatId: chat.id })
                });
                const data = await res.json();
                chat.messages.push({ role: 'ai', text: data.response });
            } catch (error) { chat.messages.push({ role: 'ai', text: 'Error de conexión' }); }
            finally {
                this.loading = false;
                this.scrollToBottom();
                this.chats = [...this.chats];
            }
        },

        scrollToBottom() { this.$nextTick(() => { const c = document.getElementById('chat-scroll-area'); if (c) c.scrollTop = c.scrollHeight; }); },

        init() {
            this.initChat();
            if (this.darkMode) document.documentElement.classList.add('dark');

            this.$watch('darkMode', val => { localStorage.setItem('theme', val ? 'dark' : 'light'); val ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark'); });
            this.$watch('zoomLevel', val => { document.documentElement.style.fontSize = val + '%'; });
            this.$watch('lang', val => localStorage.setItem('lang', val));
            this.$watch('isLoggedIn', val => localStorage.setItem('isLoggedIn', val));

            // Ejecutar lógica inicial
            this.updateLocationLogic();
            this.$watch('userProfile.country', () => { this.updateLocationLogic(); });

            this.$watch('userProfile.phone', (val) => {
                if (val) {
                    let clean = val.replace(/[^0-9]/g, ''); // Solo números
                    const max = this.userProfile.country === 'MX' ? 10 : 8;
                    if (clean.length > max) clean = clean.slice(0, max); // Recorte automático
                    if (clean !== val) this.userProfile.phone = clean;
                }
            });

            // Limpieza al cerrar modales
            this.$watch('showSettingsModal', (val) => { if (!val) this.errors = {}; });
        },

        toggleTheme() { this.darkMode = !this.darkMode; },
        adjustZoom(a) { this.zoomLevel += a; },
        resetZoom() { this.zoomLevel = 100; },
        toggleLang() { this.lang = this.lang === 'es' ? 'en' : 'es'; },
        login() { window.location.href = '/api/login'; },
        logout() { window.location.href = '/api/logout'; }

    }
}