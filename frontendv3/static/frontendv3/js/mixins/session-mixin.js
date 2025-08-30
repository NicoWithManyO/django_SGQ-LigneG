/**
 * Mixin Alpine.js pour la gestion de session
 * Évite la duplication du code de sauvegarde avec debounce
 * 
 * Usage dans un composant Alpine:
 * function myComponent() {
 *     return {
 *         ...window.sessionMixin,
 *         
 *         myField: '',
 *         
 *         init() {
 *             this.initSession();
 *             this.watchAndSave('myField', 'customKey'); // ou juste 'myField'
 *         }
 *     }
 * }
 */

window.sessionMixin = {
    // Initialisation des variables de session
    initSession() {
        this._saveTimeouts = {};
        this.DEBOUNCE_DELAY = 300;
    },
    
    /**
     * Observer un champ et le sauvegarder automatiquement en session
     * @param {string} field - Nom du champ à observer
     * @param {string} sessionKey - Clé de session (optionnel, utilise field par défaut)
     */
    watchAndSave(field, sessionKey = null) {
        const key = sessionKey || field;
        
        this.$watch(field, (value) => {
            // Annuler le timeout précédent pour ce champ
            if (this._saveTimeouts[field]) {
                clearTimeout(this._saveTimeouts[field]);
            }
            
            // Créer un nouveau timeout
            this._saveTimeouts[field] = setTimeout(() => {
                this.saveFieldToSession(key, value);
            }, this.DEBOUNCE_DELAY);
        });
    },
    
    /**
     * Observer plusieurs champs en une fois
     * @param {Array<string>|Object} fields - Liste de champs ou objet {field: sessionKey}
     */
    watchAndSaveMultiple(fields) {
        if (Array.isArray(fields)) {
            fields.forEach(field => this.watchAndSave(field));
        } else {
            Object.entries(fields).forEach(([field, sessionKey]) => {
                this.watchAndSave(field, sessionKey);
            });
        }
    },
    
    /**
     * Sauvegarder un champ immédiatement sans debounce
     * @param {string} key - Clé de session
     * @param {any} value - Valeur à sauvegarder
     */
    saveFieldToSession(key, value) {
        if (window.session && window.session.patch) {
            const data = {};
            data[key] = value;
            window.session.patch(data);
        }
    },
    
    /**
     * Sauvegarder plusieurs champs d'un coup
     * @param {Object} data - Objet avec les paires clé/valeur
     */
    saveToSession(data) {
        if (window.session && window.session.patch) {
            window.session.patch(data);
        }
    },
    
    /**
     * Nettoyer les timeouts lors de la destruction du composant
     */
    cleanupSession() {
        Object.values(this._saveTimeouts).forEach(timeout => {
            clearTimeout(timeout);
        });
        this._saveTimeouts = {};
    }
};