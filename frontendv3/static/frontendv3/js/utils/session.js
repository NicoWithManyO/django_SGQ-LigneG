/**
 * Gestion de la persistance en session Django
 * Avec debounce et gestion d'erreur améliorée
 */

class SessionManager {
    constructor() {
        this.saveQueue = {};
        this.saveTimeout = null;
        this.DEBOUNCE_DELAY = 300;
    }
    
    /**
     * Sauvegarder avec debounce
     */
    save(key, value) {
        this.saveQueue[key] = value;
        
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            this.flushQueue();
        }, this.DEBOUNCE_DELAY);
    }
    
    /**
     * Sauvegarder immédiatement
     */
    saveNow(key, value) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
        
        return fetch('/api/session/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                key: key,
                value: value
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Mettre à jour localement
            if (!window.sessionData) window.sessionData = {};
            window.sessionData[key] = value;
            return data;
        })
        .catch(error => {
            if (window.DEBUG) console.error(`Erreur de sauvegarde ${key}:`, error);
            throw error;
        });
    }
    
    /**
     * Vider la queue de sauvegarde
     */
    async flushQueue() {
        const toSave = { ...this.saveQueue };
        this.saveQueue = {};
        
        for (const [key, value] of Object.entries(toSave)) {
            try {
                await this.saveNow(key, value);
            } catch (error) {
                // Remettre dans la queue en cas d'erreur
                this.saveQueue[key] = value;
            }
        }
    }
    
    /**
     * Charger depuis la session
     */
    async load(key) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
        
        try {
            const response = await fetch(`/api/session/load/?key=${key}`, {
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return data.value;
        } catch (error) {
            if (window.DEBUG) console.error(`Erreur de chargement ${key}:`, error);
            return null;
        }
    }
    
    /**
     * Patch session (pour compatibilité)
     */
    async patch(data) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
        
        try {
            const response = await fetch('/api/session/', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            // Mettre à jour window.sessionData localement
            if (!window.sessionData) window.sessionData = {};
            for (const [key, value] of Object.entries(data)) {
                window.sessionData[key] = value;
            }
            
            return result;
        } catch (error) {
            if (window.DEBUG) console.error('Erreur de patch session:', error);
            throw error;
        }
    }
}

// Instance globale
const session = new SessionManager();

// Compatibilité avec l'ancien code
window.saveToSession = (key, value) => session.save(key, value);
window.session = session;