// API V2 - Système robuste pour la V2
const apiV2 = {
    // Configuration
    endpoints: {
        session: '/api/session/',
        profiles: '/catalog/api/profiles/',
        defectTypes: '/catalog/api/defect-types/',
        operators: '/api/operators/',
        shifts: '/api/shifts/',
        rolls: '/api/rolls/',
        productionOrders: '/api/production-orders/',
        qualityControls: '/api/quality-controls/',
        thicknessMeasurements: '/api/thickness-measurements/'
    },

    // Configuration des tentatives
    retryConfig: {
        maxRetries: 3,
        retryDelay: 1000,
        retryableErrors: [408, 429, 500, 502, 503, 504]
    },

    // Debounce pour les sauvegardes
    debounceTimers: {},
    debounceDelay: 300,

    // Cache pour éviter les requêtes inutiles
    cache: new Map(),
    cacheTimeout: 5 * 60 * 1000, // 5 minutes

    // Obtenir le CSRF token
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        
        if (cookieValue) {
            return cookieValue.split('=')[1];
        }
        
        const meta = document.querySelector('[name=csrf-token]');
        if (meta) {
            return meta.getAttribute('content');
        }
        
        console.warn('CSRF token non trouvé');
        return '';
    },

    // Headers par défaut
    getHeaders(includeContentType = true) {
        const headers = {
            'X-CSRFToken': this.getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        };
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    },

    // Gestion des erreurs avec détails
    async handleResponse(response) {
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch {
                const errorText = await response.text();
                if (errorText) errorMessage = errorText;
            }
            
            const error = new Error(errorMessage);
            error.status = response.status;
            throw error;
        }
        
        // Gérer les réponses vides (204 No Content)
        if (response.status === 204) {
            return null;
        }
        
        return response.json();
    },

    // Retry automatique pour les erreurs temporaires
    async fetchWithRetry(url, options = {}, retries = 0) {
        try {
            const response = await fetch(url, options);
            return response;
        } catch (error) {
            if (retries < this.retryConfig.maxRetries) {
                console.warn(`Tentative ${retries + 1}/${this.retryConfig.maxRetries} échouée, nouvelle tentative...`);
                await new Promise(resolve => setTimeout(resolve, this.retryConfig.retryDelay));
                return this.fetchWithRetry(url, options, retries + 1);
            }
            throw error;
        }
    },

    // Requête générique avec gestion d'erreur
    async request(url, options = {}) {
        try {
            const response = await this.fetchWithRetry(url, {
                ...options,
                headers: {
                    ...this.getHeaders(options.includeContentType !== false),
                    ...options.headers
                }
            });

            // Retry sur certains codes d'erreur
            if (this.retryConfig.retryableErrors.includes(response.status)) {
                throw new Error(`Status ${response.status} - retryable`);
            }

            return await this.handleResponse(response);
        } catch (error) {
            console.error(`Erreur API ${options.method || 'GET'} ${url}:`, error);
            throw error;
        }
    },

    // GET avec cache
    async get(endpoint, useCache = true) {
        const cacheKey = `GET:${endpoint}`;
        
        // Vérifier le cache
        if (useCache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        const data = await this.request(endpoint);
        
        // Mettre en cache
        if (useCache && data !== null) {
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
        }

        return data;
    },

    // POST
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // PATCH
    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    // DELETE
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    },

    // Session - Récupérer
    async getSession() {
        try {
            return await this.get(this.endpoints.session, false); // Pas de cache pour la session
        } catch (error) {
            console.error('Erreur récupération session:', error);
            return {};
        }
    },

    // Session - Sauvegarder avec debounce
    saveToSession(data) {
        // Clear previous timer
        if (this.debounceTimers.session) {
            clearTimeout(this.debounceTimers.session);
        }

        // Return promise pour await
        return new Promise((resolve, reject) => {
            this.debounceTimers.session = setTimeout(async () => {
                try {
                    console.log('📤 Actually sending to backend:', data);
                    const result = await this.patch(this.endpoints.session, data);
                    console.log('✅ Backend response:', result);
                    resolve(result);
                } catch (error) {
                    console.error('❌ Backend error:', error);
                    reject(error);
                }
            }, this.debounceDelay);
        });
    },

    // Méthodes spécifiques pour chaque ressource
    async getProfiles() {
        return this.get(this.endpoints.profiles);
    },

    async getDefectTypes() {
        return this.get(this.endpoints.defectTypes);
    },

    async getOperators() {
        return this.get(this.endpoints.operators);
    },

    async createShift(shiftData) {
        return this.post(this.endpoints.shifts, shiftData);
    },

    async updateShift(shiftId, shiftData) {
        return this.patch(`${this.endpoints.shifts}${shiftId}/`, shiftData);
    },

    async createRoll(rollData) {
        return this.post(this.endpoints.rolls, rollData);
    },

    async updateRoll(rollId, rollData) {
        return this.patch(`${this.endpoints.rolls}${rollId}/`, rollData);
    },

    async saveQualityControl(controlData) {
        return this.post(this.endpoints.qualityControls, controlData);
    },

    async saveThicknessMeasurement(measurementData) {
        return this.post(this.endpoints.thicknessMeasurements, measurementData);
    },

    // Clear cache
    clearCache() {
        this.cache.clear();
    },

    // Clear cache pour un endpoint spécifique
    clearEndpointCache(endpoint) {
        const cacheKey = `GET:${endpoint}`;
        this.cache.delete(cacheKey);
    }
};

// Export pour utilisation globale
window.apiV2 = apiV2;
window.api = apiV2; // Alias pour compatibilité avec SyncEngine