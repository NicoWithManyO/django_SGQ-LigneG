/**
 * Registry centralisé des composants Alpine.js
 * Évite les querySelector fragiles et gère l'ordre d'initialisation
 */

window.componentRegistry = {
    // Stockage des composants enregistrés
    components: new Map(),
    
    // File d'attente pour les composants en attente
    waitingQueue: new Map(),
    
    // Configuration
    debug: window.DEBUG || false,
    
    /**
     * Enregistrer un composant
     * @param {string} name - Nom du composant
     * @param {Object} component - Instance du composant Alpine
     */
    register(name, component) {
        if (this.debug) {
            debug(`ComponentRegistry: Enregistrement de "${name}"`);
        }
        
        // Stocker le composant
        this.components.set(name, component);
        
        // Vérifier si des composants attendent celui-ci
        if (this.waitingQueue.has(name)) {
            const callbacks = this.waitingQueue.get(name);
            callbacks.forEach(callback => {
                try {
                    callback(component);
                } catch (error) {
                    console.error(`Erreur callback pour ${name}:`, error);
                }
            });
            this.waitingQueue.delete(name);
        }
        
        // Émettre un événement
        window.eventBus?.emit(`component:registered`, { name, component });
    },
    
    /**
     * Désenregistrer un composant
     * @param {string} name - Nom du composant
     */
    unregister(name) {
        if (this.debug) {
            debug(`ComponentRegistry: Désenregistrement de "${name}"`);
        }
        
        this.components.delete(name);
        window.eventBus?.emit(`component:unregistered`, { name });
    },
    
    /**
     * Obtenir un composant
     * @param {string} name - Nom du composant
     * @returns {Object|null} Instance du composant ou null
     */
    get(name) {
        return this.components.get(name) || null;
    },
    
    /**
     * Attendre qu'un composant soit disponible
     * @param {string} name - Nom du composant
     * @param {Function} callback - Fonction à appeler quand disponible
     * @param {number} timeout - Timeout en ms (défaut: 5000)
     * @returns {Promise} Promise qui se résout avec le composant
     */
    waitFor(name, callback = null, timeout = 5000) {
        return new Promise((resolve, reject) => {
            // Si déjà disponible
            const component = this.get(name);
            if (component) {
                if (callback) callback(component);
                resolve(component);
                return;
            }
            
            // Sinon, ajouter à la file d'attente
            if (!this.waitingQueue.has(name)) {
                this.waitingQueue.set(name, []);
            }
            
            const timeoutId = setTimeout(() => {
                reject(new Error(`Timeout en attendant le composant "${name}"`));
            }, timeout);
            
            const wrappedCallback = (component) => {
                clearTimeout(timeoutId);
                if (callback) callback(component);
                resolve(component);
            };
            
            this.waitingQueue.get(name).push(wrappedCallback);
        });
    },
    
    /**
     * Vérifier si un composant est enregistré
     * @param {string} name - Nom du composant
     * @returns {boolean}
     */
    has(name) {
        return this.components.has(name);
    },
    
    /**
     * Obtenir tous les composants enregistrés
     * @returns {Object} Map des composants
     */
    getAll() {
        return Object.fromEntries(this.components);
    },
    
    /**
     * Appeler une méthode sur un composant
     * @param {string} name - Nom du composant
     * @param {string} method - Nom de la méthode
     * @param {Array} args - Arguments à passer
     * @returns {any} Résultat de l'appel
     */
    call(name, method, ...args) {
        const component = this.get(name);
        
        if (!component) {
            throw new Error(`Composant "${name}" non trouvé`);
        }
        
        if (typeof component[method] !== 'function') {
            throw new Error(`Méthode "${method}" non trouvée sur "${name}"`);
        }
        
        return component[method].apply(component, args);
    },
    
    /**
     * Vérifier les dépendances entre composants
     * @returns {Object} Rapport des dépendances
     */
    checkDependencies() {
        const report = {
            registered: Array.from(this.components.keys()),
            waiting: {},
            healthy: true
        };
        
        // Lister les composants en attente
        this.waitingQueue.forEach((callbacks, name) => {
            report.waiting[name] = callbacks.length;
            report.healthy = false;
        });
        
        return report;
    },
    
    /**
     * Helper pour initialiser un composant avec le registry
     * À utiliser dans la fonction init() des composants Alpine
     * @param {Object} component - Instance du composant (this)
     * @param {string} name - Nom pour l'enregistrement
     */
    initComponent(component, name) {
        // Enregistrer le composant
        this.register(name, component);
        
        // Ajouter une méthode de nettoyage
        const originalDestroy = component.$destroy;
        component.$destroy = function() {
            window.componentRegistry.unregister(name);
            if (originalDestroy) originalDestroy.call(this);
        };
        
        if (this.debug) {
            debug(`ComponentRegistry: ${name} initialisé`);
        }
    },
    
    /**
     * Reset complet du registry (pour tests)
     */
    reset() {
        this.components.clear();
        this.waitingQueue.clear();
        if (this.debug) {
            debug('ComponentRegistry: Reset complet');
        }
    }
};

// Helper global pour accès rapide
window.getComponent = (name) => window.componentRegistry.get(name);
window.waitForComponent = (name, timeout) => window.componentRegistry.waitFor(name, null, timeout);

// Export
window.ComponentRegistry = window.componentRegistry;