/**
 * Service Event Bus centralisé
 * Gère tous les événements de l'application V3
 * Permet le debugging et évite les dépendances circulaires
 */

window.eventBus = {
    // Stockage des listeners pour debugging
    listeners: new Map(),
    
    // Log des événements pour debug
    eventLog: [],
    maxLogSize: 100,
    
    // Configuration
    debug: window.DEBUG || false,
    
    /**
     * Émettre un événement
     * @param {string} eventName - Nom de l'événement (format recommandé: "domain:action")
     * @param {any} detail - Données de l'événement
     * @param {Element} target - Élément cible (défaut: window)
     */
    emit(eventName, detail = {}, target = window) {
        // Log pour debug
        if (this.debug) {
            this.logEvent('emit', eventName, detail);
        }
        
        // Créer et dispatcher l'événement
        const event = new CustomEvent(eventName, { 
            detail,
            bubbles: true,
            cancelable: true
        });
        
        target.dispatchEvent(event);
        
        return event;
    },
    
    /**
     * Écouter un événement
     * @param {string} eventName - Nom de l'événement
     * @param {Function} callback - Fonction callback
     * @param {Element} target - Élément cible (défaut: window)
     * @param {Object} options - Options addEventListener
     * @returns {Function} Fonction pour retirer le listener
     */
    on(eventName, callback, target = window, options = {}) {
        // Wrapper pour logging
        const wrappedCallback = (event) => {
            if (this.debug) {
                this.logEvent('receive', eventName, event.detail);
            }
            callback(event);
        };
        
        // Stocker pour debug
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }
        this.listeners.get(eventName).push({
            callback: callback.name || 'anonymous',
            target: target.tagName || 'window'
        });
        
        // Ajouter le listener
        target.addEventListener(eventName, wrappedCallback, options);
        
        // Retourner fonction de nettoyage
        return () => {
            target.removeEventListener(eventName, wrappedCallback, options);
        };
    },
    
    /**
     * Écouter un événement une seule fois
     */
    once(eventName, callback, target = window) {
        return this.on(eventName, callback, target, { once: true });
    },
    
    /**
     * Logger un événement
     */
    logEvent(type, eventName, detail) {
        const entry = {
            type,
            eventName,
            detail: detail ? JSON.parse(JSON.stringify(detail)) : null,
            timestamp: new Date().toISOString(),
            stack: new Error().stack
        };
        
        this.eventLog.push(entry);
        
        // Limiter la taille du log
        if (this.eventLog.length > this.maxLogSize) {
            this.eventLog.shift();
        }
        
        debug(`EventBus ${type}: ${eventName}`, detail);
    },
    
    /**
     * Obtenir l'historique des événements
     */
    getEventHistory(eventName = null) {
        if (eventName) {
            return this.eventLog.filter(e => e.eventName === eventName);
        }
        return [...this.eventLog];
    },
    
    /**
     * Obtenir les listeners enregistrés
     */
    getListeners(eventName = null) {
        if (eventName) {
            return this.listeners.get(eventName) || [];
        }
        return Object.fromEntries(this.listeners);
    },
    
    /**
     * Vider les logs
     */
    clearLogs() {
        this.eventLog = [];
    },
    
    /**
     * Analyser les dépendances entre événements
     */
    analyzeDependencies() {
        const emitters = {};
        const receivers = {};
        
        // Parcourir l'historique
        this.eventLog.forEach(entry => {
            // Extraire le composant depuis la stack trace
            const stackLines = entry.stack.split('\n');
            const callerLine = stackLines[3] || '';
            const match = callerLine.match(/at (\w+)\./);
            const component = match ? match[1] : 'unknown';
            
            if (entry.type === 'emit') {
                if (!emitters[entry.eventName]) {
                    emitters[entry.eventName] = new Set();
                }
                emitters[entry.eventName].add(component);
            }
        });
        
        // Croiser avec les listeners
        this.listeners.forEach((listeners, eventName) => {
            receivers[eventName] = listeners.map(l => l.callback);
        });
        
        return { emitters, receivers };
    }
};

// Définition des événements standard V3
window.eventBus.EVENTS = {
    // Shift
    SHIFT_SAVED: 'shift:saved',
    SHIFT_DATA_CHANGED: 'shift:data-changed',
    SHIFT_VALIDATED: 'shift:validated',
    
    // Roll  
    ROLL_SAVED: 'roll:saved',
    ROLL_RESET: 'roll:reset',
    ROLL_NUMBER_CHANGED: 'roll:number-changed',
    ROLL_CONFORMITY_CHANGED: 'roll:conformity-changed',
    
    // OF
    OF_CHANGED: 'of:changed',
    OF_LOADED: 'of:loaded',
    TARGET_LENGTH_CHANGED: 'target-length:changed',
    
    // Profile
    PROFILE_CHANGED: 'profile:changed',
    PROFILE_LOADED: 'profile:loaded',
    
    // QC
    QC_STATUS_CHANGED: 'qc:status-changed',
    QC_BADGE_CHANGED: 'qc:badge-changed',
    
    // Grammage
    GRAMMAGE_STATUS_CHANGED: 'grammage:status-changed',
    
    // Session
    SESSION_UPDATED: 'session:updated',
    SESSION_CLEARED: 'session:cleared',
    
    // KPI
    KPI_UPDATED: 'kpi:updated',
    
    // UI
    FILL_QC_RANDOM: 'ui:fill-qc-random',
    MODAL_SHOW: 'ui:modal-show',
    MODAL_HIDE: 'ui:modal-hide'
};

// Migrer progressivement les anciens noms vers les nouveaux
window.eventBus.LEGACY_MAP = {
    'shift-saved': window.eventBus.EVENTS.SHIFT_SAVED,
    'shift-data-changed': window.eventBus.EVENTS.SHIFT_DATA_CHANGED,
    'roll-saved': window.eventBus.EVENTS.ROLL_SAVED,
    'roll-reset': window.eventBus.EVENTS.ROLL_RESET,
    'roll-number-changed': window.eventBus.EVENTS.ROLL_NUMBER_CHANGED,
    'roll-conformity-changed': window.eventBus.EVENTS.ROLL_CONFORMITY_CHANGED,
    'of-changed': window.eventBus.EVENTS.OF_CHANGED,
    'profile-changed': window.eventBus.EVENTS.PROFILE_CHANGED,
    'qc-status-changed': window.eventBus.EVENTS.QC_STATUS_CHANGED,
    'qc-badge-changed': window.eventBus.EVENTS.QC_BADGE_CHANGED,
    'grammage-status-changed': window.eventBus.EVENTS.GRAMMAGE_STATUS_CHANGED,
    'session-updated': window.eventBus.EVENTS.SESSION_UPDATED,
    'kpi-updated': window.eventBus.EVENTS.KPI_UPDATED,
    'fill-qc-random': window.eventBus.EVENTS.FILL_QC_RANDOM
};

// Intercepter les anciens événements pour migration progressive
if (window.eventBus.debug) {
    const originalDispatchEvent = EventTarget.prototype.dispatchEvent;
    EventTarget.prototype.dispatchEvent = function(event) {
        if (event instanceof CustomEvent && window.eventBus.LEGACY_MAP[event.type]) {
            console.warn(`[EventBus] Événement legacy détecté: "${event.type}". Utiliser plutôt: "${window.eventBus.LEGACY_MAP[event.type]}"`);
        }
        return originalDispatchEvent.call(this, event);
    };
}

// Exposer globalement
window.EventBus = window.eventBus;