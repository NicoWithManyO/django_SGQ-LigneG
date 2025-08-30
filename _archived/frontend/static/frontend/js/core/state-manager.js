/**
 * StateManager - Gestionnaire d'état centralisé pour l'application
 * 
 * Fournit un état immutable avec historique, notifications et middleware
 */
class StateManager {
    constructor() {
        this.state = {};
        this.subscribers = new Map();
        this.middleware = [];
        this.history = [];
        this.maxHistory = 1000;
        this.debug = window.DEBUG || false;
    }
    
    /**
     * Définir une valeur dans l'état
     * @param {string} path - Chemin vers la propriété (ex: 'shift.operatorId')
     * @param {*} value - Nouvelle valeur
     * @param {string} source - Source du changement ('user', 'api', 'system')
     */
    setState(path, value, source = 'user') {
        const oldValue = this.getState(path);
        const timestamp = Date.now();
        
        // Si la valeur n'a pas changé, ne rien faire
        if (this._deepEqual(oldValue, value)) {
            return;
        }
        
        // Passer par les middlewares
        let processedValue = value;
        for (const mw of this.middleware) {
            try {
                processedValue = mw({
                    path,
                    value: processedValue,
                    oldValue,
                    source,
                    timestamp,
                    state: this.state
                });
            } catch (error) {
                console.error('Middleware error:', error);
                // En cas d'erreur, continuer avec la valeur originale
            }
        }
        
        // Créer une entrée d'historique
        const historyEntry = {
            id: this._generateId(),
            timestamp,
            path,
            oldValue: this._deepClone(oldValue),
            newValue: this._deepClone(processedValue),
            source
        };
        
        // Ajouter à l'historique
        this.history.push(historyEntry);
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }
        
        // Mettre à jour l'état
        this._setDeep(this.state, path, processedValue);
        
        // Logger en mode debug
        if (this.debug || path.includes('longueurCible')) {
            console.log(`🔄 State change: ${path}`, {
                oldValue,
                newValue: processedValue,
                source
            });
        }
        
        // Notifier les souscripteurs
        this._notify(path, processedValue, oldValue, source);
    }
    
    /**
     * Obtenir une valeur de l'état
     * @param {string} path - Chemin vers la propriété
     * @param {*} defaultValue - Valeur par défaut si non trouvée
     */
    getState(path, defaultValue = undefined) {
        if (!path) return this.state;
        
        const keys = path.split('.');
        let current = this.state;
        
        for (const key of keys) {
            if (current && typeof current === 'object' && key in current) {
                current = current[key];
            } else {
                return defaultValue;
            }
        }
        
        return current;
    }
    
    /**
     * Observer les changements sur un chemin
     * @param {string} path - Chemin à observer (* pour tout)
     * @param {Function} callback - Fonction appelée lors des changements
     * @returns {Function} Fonction de désinscription
     */
    subscribe(path, callback) {
        if (!this.subscribers.has(path)) {
            this.subscribers.set(path, new Set());
        }
        this.subscribers.get(path).add(callback);
        
        // Retourner une fonction de désinscription
        return () => {
            const subs = this.subscribers.get(path);
            if (subs) {
                subs.delete(callback);
                if (subs.size === 0) {
                    this.subscribers.delete(path);
                }
            }
        };
    }
    
    /**
     * Ajouter un middleware
     * @param {Function} middleware - Fonction middleware
     */
    use(middleware) {
        if (typeof middleware === 'function') {
            this.middleware.push(middleware);
        }
    }
    
    /**
     * Obtenir l'historique des changements
     * @param {Object} filter - Filtres optionnels
     */
    getHistory(filter = {}) {
        let history = [...this.history];
        
        if (filter.path) {
            history = history.filter(h => h.path.startsWith(filter.path));
        }
        
        if (filter.source) {
            history = history.filter(h => h.source === filter.source);
        }
        
        if (filter.since) {
            history = history.filter(h => h.timestamp > filter.since);
        }
        
        if (filter.limit) {
            history = history.slice(-filter.limit);
        }
        
        return history;
    }
    
    /**
     * Réinitialiser une partie de l'état
     * @param {string} path - Chemin à réinitialiser
     */
    reset(path) {
        if (!path) {
            // Réinitialiser tout l'état
            const oldState = this._deepClone(this.state);
            this.state = {};
            this._notify('*', {}, oldState, 'system');
        } else {
            // Réinitialiser un chemin spécifique
            this.setState(path, undefined, 'system');
        }
    }
    
    /**
     * Créer un snapshot de l'état actuel
     */
    snapshot() {
        return {
            state: this._deepClone(this.state),
            timestamp: Date.now()
        };
    }
    
    /**
     * Restaurer l'état depuis un snapshot
     */
    restore(snapshot) {
        if (snapshot && snapshot.state) {
            const oldState = this._deepClone(this.state);
            this.state = this._deepClone(snapshot.state);
            this._notify('*', this.state, oldState, 'system');
        }
    }
    
    // Méthodes privées
    
    _setDeep(obj, path, value) {
        const keys = path.split('.');
        let current = obj;
        
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(key in current) || typeof current[key] !== 'object') {
                current[key] = {};
            }
            current = current[key];
        }
        
        const lastKey = keys[keys.length - 1];
        if (value === undefined) {
            delete current[lastKey];
        } else {
            current[lastKey] = value;
        }
    }
    
    _notify(path, newValue, oldValue, source) {
        // Notifier les abonnés exacts
        const exactSubs = this.subscribers.get(path);
        if (exactSubs) {
            exactSubs.forEach(callback => {
                try {
                    callback(newValue, oldValue, source);
                } catch (error) {
                    console.error('Subscriber error:', error);
                }
            });
        }
        
        // Notifier les abonnés wildcard
        const wildcardSubs = this.subscribers.get('*');
        if (wildcardSubs) {
            wildcardSubs.forEach(callback => {
                try {
                    callback({ path, newValue, oldValue, source });
                } catch (error) {
                    console.error('Wildcard subscriber error:', error);
                }
            });
        }
        
        // Notifier les abonnés de chemins parents
        const pathParts = path.split('.');
        for (let i = pathParts.length - 1; i > 0; i--) {
            const parentPath = pathParts.slice(0, i).join('.');
            const parentSubs = this.subscribers.get(parentPath + '.*');
            if (parentSubs) {
                parentSubs.forEach(callback => {
                    try {
                        callback({ path, newValue, oldValue, source });
                    } catch (error) {
                        console.error('Parent subscriber error:', error);
                    }
                });
            }
        }
    }
    
    _deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this._deepClone(item));
        if (obj instanceof Object) {
            const cloned = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    cloned[key] = this._deepClone(obj[key]);
                }
            }
            return cloned;
        }
    }
    
    _deepEqual(a, b) {
        if (a === b) return true;
        if (a == null || b == null) return false;
        if (typeof a !== typeof b) return false;
        
        if (typeof a !== 'object') return a === b;
        
        if (Array.isArray(a)) {
            if (!Array.isArray(b) || a.length !== b.length) return false;
            return a.every((item, i) => this._deepEqual(item, b[i]));
        }
        
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);
        
        if (keysA.length !== keysB.length) return false;
        
        return keysA.every(key => this._deepEqual(a[key], b[key]));
    }
    
    _generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// Créer l'instance globale
window.stateManager = new StateManager();

// Middleware de logging en développement
if (window.DEBUG) {
    window.stateManager.use(({ path, value, oldValue, source }) => {
        console.group(`State Change: ${path}`);
        console.log('Old:', oldValue);
        console.log('New:', value);
        console.log('Source:', source);
        console.groupEnd();
        return value;
    });
}

// Exposer pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateManager;
}