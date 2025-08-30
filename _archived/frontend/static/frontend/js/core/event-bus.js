/**
 * EventBus - Système d'événements amélioré
 * 
 * Gère la communication entre composants avec historique et priorités
 */
class EventBus {
    constructor() {
        this.listeners = new Map();
        this.history = [];
        this.maxHistory = 1000;
        this.debug = window.DEBUG || false;
        this.eventStats = new Map();
        
        // Configuration
        this.config = {
            bubbles: true,
            cancelable: true,
            composed: true
        };
        
        // File de priorité pour les listeners
        this.priorityQueues = new Map();
    }
    
    /**
     * Émettre un événement
     * @param {string} eventName - Nom de l'événement
     * @param {*} payload - Données de l'événement
     * @param {Object} metadata - Métadonnées optionnelles
     */
    emit(eventName, payload, metadata = {}) {
        const event = {
            id: this._generateId(),
            name: eventName,
            payload: this._cloneDeep(payload),
            metadata: {
                ...metadata,
                timestamp: Date.now(),
                source: this._getCallerInfo()
            }
        };
        
        // Ajouter à l'historique
        this._addToHistory(event);
        
        // Mettre à jour les statistiques
        this._updateStats(eventName);
        
        // Logger en mode debug
        if (this.debug) {
            console.log(`📢 Event: ${eventName}`, payload);
        }
        
        // Créer et dispatcher l'événement DOM
        const customEvent = new CustomEvent(eventName, {
            detail: payload,
            bubbles: this.config.bubbles,
            cancelable: this.config.cancelable,
            composed: this.config.composed
        });
        
        // Ajouter les métadonnées à l'événement
        customEvent.eventId = event.id;
        customEvent.metadata = event.metadata;
        
        // Dispatcher
        const result = window.dispatchEvent(customEvent);
        
        // Si l'événement a été annulé
        if (!result && this.debug) {
            console.warn(`Event ${eventName} was cancelled`);
        }
        
        return event.id;
    }
    
    /**
     * S'abonner à un événement avec priorité
     * @param {string} eventName - Nom de l'événement
     * @param {Function} handler - Fonction à exécuter
     * @param {number} priority - Priorité (0 = haute)
     * @param {Object} options - Options d'abonnement
     */
    on(eventName, handler, priority = 0, options = {}) {
        if (!eventName || typeof handler !== 'function') {
            throw new Error('Event name and handler function are required');
        }
        
        // Créer la queue de priorité si nécessaire
        if (!this.priorityQueues.has(eventName)) {
            this.priorityQueues.set(eventName, new PriorityQueue());
        }
        
        // Wrapper pour capturer les erreurs et ajouter le contexte
        const wrappedHandler = (event) => {
            try {
                // Ajouter le contexte de l'événement
                const context = {
                    eventId: event.eventId,
                    metadata: event.metadata,
                    preventDefault: () => event.preventDefault(),
                    stopPropagation: () => event.stopPropagation()
                };
                
                // Appeler le handler
                const result = handler(event.detail, context, event);
                
                // Si le handler retourne false, annuler l'événement
                if (result === false && event.cancelable) {
                    event.preventDefault();
                }
                
                return result;
            } catch (error) {
                console.error(`Handler error for ${eventName}:`, error);
                
                // Émettre un événement d'erreur
                this.emit('error', {
                    eventName,
                    error: error.message,
                    stack: error.stack
                }, { source: 'event-handler' });
            }
        };
        
        // Stocker les informations du listener
        const listenerInfo = {
            id: this._generateId(),
            eventName,
            handler,
            wrappedHandler,
            priority,
            options,
            subscribeTime: Date.now()
        };
        
        // Ajouter à la queue de priorité
        this.priorityQueues.get(eventName).add(listenerInfo, priority);
        
        // Ajouter le listener DOM
        const eventOptions = {
            capture: options.capture || false,
            passive: options.passive !== false,
            once: options.once || false
        };
        
        window.addEventListener(eventName, wrappedHandler, eventOptions);
        
        // Retourner une fonction de désinscription
        return () => this.off(eventName, listenerInfo.id);
    }
    
    /**
     * Alias pour on()
     */
    subscribe(eventName, handler, priority, options) {
        return this.on(eventName, handler, priority, options);
    }
    
    /**
     * S'abonner une seule fois
     */
    once(eventName, handler, priority = 0) {
        return this.on(eventName, handler, priority, { once: true });
    }
    
    /**
     * Se désabonner d'un événement
     * @param {string} eventName - Nom de l'événement
     * @param {string} listenerId - ID du listener
     */
    off(eventName, listenerId) {
        const queue = this.priorityQueues.get(eventName);
        if (!queue) return;
        
        const listenerInfo = queue.findById(listenerId);
        if (!listenerInfo) return;
        
        // Retirer le listener DOM
        window.removeEventListener(eventName, listenerInfo.wrappedHandler);
        
        // Retirer de la queue
        queue.removeById(listenerId);
        
        // Nettoyer si la queue est vide
        if (queue.isEmpty()) {
            this.priorityQueues.delete(eventName);
        }
    }
    
    /**
     * Retirer tous les listeners d'un événement
     */
    offAll(eventName) {
        const queue = this.priorityQueues.get(eventName);
        if (!queue) return;
        
        // Retirer tous les listeners DOM
        queue.forEach(listenerInfo => {
            window.removeEventListener(eventName, listenerInfo.wrappedHandler);
        });
        
        // Supprimer la queue
        this.priorityQueues.delete(eventName);
    }
    
    /**
     * Obtenir l'historique des événements
     * @param {Object} filter - Filtres optionnels
     */
    getHistory(filter = {}) {
        let history = [...this.history];
        
        if (filter.name) {
            history = history.filter(e => e.name === filter.name);
        }
        
        if (filter.since) {
            history = history.filter(e => e.metadata.timestamp > filter.since);
        }
        
        if (filter.source) {
            history = history.filter(e => e.metadata.source === filter.source);
        }
        
        if (filter.limit) {
            history = history.slice(-filter.limit);
        }
        
        return history;
    }
    
    /**
     * Obtenir les statistiques des événements
     */
    getStats(eventName = null) {
        if (eventName) {
            return this.eventStats.get(eventName) || {
                count: 0,
                lastEmitted: null,
                listeners: 0
            };
        }
        
        const stats = {};
        for (const [name, stat] of this.eventStats) {
            stats[name] = {
                ...stat,
                listeners: this.priorityQueues.has(name) ? 
                    this.priorityQueues.get(name).size() : 0
            };
        }
        
        return stats;
    }
    
    /**
     * Attendre qu'un événement soit émis
     * @param {string} eventName - Nom de l'événement
     * @param {number} timeout - Timeout en ms (optionnel)
     */
    waitFor(eventName, timeout = 0) {
        return new Promise((resolve, reject) => {
            let timeoutId;
            
            const cleanup = () => {
                if (timeoutId) clearTimeout(timeoutId);
                this.off(eventName, listenerId);
            };
            
            const listenerId = this.once(eventName, (payload) => {
                cleanup();
                resolve(payload);
            });
            
            if (timeout > 0) {
                timeoutId = setTimeout(() => {
                    cleanup();
                    reject(new Error(`Timeout waiting for event: ${eventName}`));
                }, timeout);
            }
        });
    }
    
    /**
     * Créer un canal d'événements typés
     * @param {string} channelName - Nom du canal
     */
    channel(channelName) {
        const self = this;
        
        return {
            emit: (payload, metadata) => 
                self.emit(`${channelName}:message`, payload, metadata),
                
            on: (handler, priority, options) => 
                self.on(`${channelName}:message`, handler, priority, options),
                
            once: (handler, priority) => 
                self.once(`${channelName}:message`, handler, priority),
                
            off: (listenerId) => 
                self.off(`${channelName}:message`, listenerId),
                
            broadcast: (type, payload, metadata) => 
                self.emit(`${channelName}:${type}`, payload, metadata),
                
            subscribe: (type, handler, priority, options) => 
                self.on(`${channelName}:${type}`, handler, priority, options)
        };
    }
    
    // Méthodes privées
    
    _addToHistory(event) {
        this.history.push(event);
        
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }
    }
    
    _updateStats(eventName) {
        const stats = this.eventStats.get(eventName) || {
            count: 0,
            firstEmitted: Date.now(),
            lastEmitted: null
        };
        
        stats.count++;
        stats.lastEmitted = Date.now();
        
        this.eventStats.set(eventName, stats);
    }
    
    _getCallerInfo() {
        try {
            const stack = new Error().stack;
            const lines = stack.split('\n');
            
            // Trouver la ligne qui a appelé emit()
            for (let i = 3; i < lines.length && i < 6; i++) {
                const line = lines[i].trim();
                if (!line.includes('event-bus.js') && 
                    !line.includes('EventBus')) {
                    return line;
                }
            }
        } catch (e) {
            // Ignorer les erreurs
        }
        
        return 'unknown';
    }
    
    _generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    _cloneDeep(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this._cloneDeep(item));
        if (obj instanceof Object) {
            const cloned = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    cloned[key] = this._cloneDeep(obj[key]);
                }
            }
            return cloned;
        }
    }
}

/**
 * File de priorité simple
 */
class PriorityQueue {
    constructor() {
        this.items = [];
    }
    
    add(item, priority) {
        item.priority = priority;
        
        // Insérer à la bonne position
        let added = false;
        for (let i = 0; i < this.items.length; i++) {
            if (priority < this.items[i].priority) {
                this.items.splice(i, 0, item);
                added = true;
                break;
            }
        }
        
        if (!added) {
            this.items.push(item);
        }
    }
    
    findById(id) {
        return this.items.find(item => item.id === id);
    }
    
    removeById(id) {
        const index = this.items.findIndex(item => item.id === id);
        if (index > -1) {
            this.items.splice(index, 1);
        }
    }
    
    forEach(callback) {
        this.items.forEach(callback);
    }
    
    size() {
        return this.items.length;
    }
    
    isEmpty() {
        return this.items.length === 0;
    }
}

// Créer l'instance globale
window.eventBus = new EventBus();

// Exposer pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EventBus, PriorityQueue };
}