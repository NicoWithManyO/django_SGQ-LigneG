/**
 * Mixin pour gérer les watchers de façon optimisée
 * Évite la duplication de code et optimise les performances
 */
window.watcherMixin = {
    // Map pour stocker les timeouts de debounce
    _watcherTimeouts: {},
    
    // Map pour stocker les valeurs précédentes (pour éviter les updates inutiles)
    _watcherPreviousValues: {},
    
    /**
     * Créer un watcher optimisé avec debounce et vérification de changement
     * @param {string|function} target - Propriété à observer ou fonction getter
     * @param {function} callback - Fonction à appeler lors du changement
     * @param {Object} options - Options du watcher
     */
    watchOptimized(target, callback, options = {}) {
        const {
            debounce = 300,
            immediate = false,
            deep = false,
            skipEqual = true
        } = options;
        
        // Générer une clé unique pour ce watcher
        const watcherKey = typeof target === 'string' ? target : target.toString();
        
        // Wrapper pour gérer debounce et comparaison
        const watcherWrapper = (newValue, oldValue) => {
            // Si skipEqual, vérifier si la valeur a vraiment changé
            if (skipEqual && this._isEqual(newValue, oldValue)) {
                return;
            }
            
            // Stocker la nouvelle valeur
            this._watcherPreviousValues[watcherKey] = this._deepClone(newValue);
            
            // Si pas de debounce, exécuter immédiatement
            if (!debounce) {
                callback.call(this, newValue, oldValue);
                return;
            }
            
            // Annuler le timeout précédent
            if (this._watcherTimeouts[watcherKey]) {
                clearTimeout(this._watcherTimeouts[watcherKey]);
            }
            
            // Créer un nouveau timeout
            this._watcherTimeouts[watcherKey] = setTimeout(() => {
                callback.call(this, newValue, oldValue);
                delete this._watcherTimeouts[watcherKey];
            }, debounce);
        };
        
        // Créer le watcher Alpine
        this.$watch(target, watcherWrapper, { deep });
        
        // Si immediate, exécuter une fois au démarrage
        if (immediate) {
            const initialValue = typeof target === 'string' ? this[target] : target.call(this);
            callback.call(this, initialValue, undefined);
        }
    },
    
    /**
     * Créer plusieurs watchers pour sauvegarder dans la session
     * @param {Array<string>} fields - Liste des champs à observer
     * @param {string} sessionKey - Clé de session principale
     * @param {Object} options - Options communes aux watchers
     */
    watchAndSaveMultiple(fields, sessionKey, options = {}) {
        const {
            debounce = 300,
            transform = null
        } = options;
        
        fields.forEach(field => {
            this.watchOptimized(field, (newValue) => {
                // Appliquer la transformation si fournie
                const valueToSave = transform ? transform(field, newValue) : newValue;
                
                // Construire l'objet de données
                const data = {};
                data[`${sessionKey}_${field}`] = valueToSave;
                
                // Sauvegarder via le mixin session ou directement
                if (this.saveToSession) {
                    this.saveToSession(data);
                } else if (window.session) {
                    window.session.patch(data);
                }
            }, { debounce });
        });
    },
    
    /**
     * Créer un watcher composite pour plusieurs propriétés
     * @param {Array<string>} properties - Propriétés à observer
     * @param {function} callback - Fonction appelée avec toutes les valeurs
     * @param {Object} options - Options du watcher
     */
    watchComposite(properties, callback, options = {}) {
        const {
            debounce = 300,
            immediate = false
        } = options;
        
        // Créer une fonction getter qui retourne toutes les valeurs
        const getter = () => {
            const values = {};
            properties.forEach(prop => {
                values[prop] = this[prop];
            });
            return values;
        };
        
        // Utiliser watchOptimized avec le getter
        this.watchOptimized(getter, (newValues, oldValues) => {
            callback.call(this, newValues, oldValues);
        }, { ...options, deep: true });
    },
    
    /**
     * Nettoyer tous les watchers (à appeler dans destroy)
     */
    cleanupWatchers() {
        // Annuler tous les timeouts en cours
        Object.values(this._watcherTimeouts).forEach(timeout => {
            clearTimeout(timeout);
        });
        this._watcherTimeouts = {};
        this._watcherPreviousValues = {};
    },
    
    /**
     * Vérifier l'égalité profonde entre deux valeurs
     * @private
     */
    _isEqual(a, b) {
        if (a === b) return true;
        if (a == null || b == null) return false;
        if (typeof a !== typeof b) return false;
        
        if (typeof a === 'object') {
            const keysA = Object.keys(a);
            const keysB = Object.keys(b);
            if (keysA.length !== keysB.length) return false;
            
            return keysA.every(key => this._isEqual(a[key], b[key]));
        }
        
        return false;
    },
    
    /**
     * Clone profond d'une valeur
     * @private
     */
    _deepClone(value) {
        if (value == null || typeof value !== 'object') return value;
        if (value instanceof Date) return new Date(value);
        if (value instanceof Array) return value.map(item => this._deepClone(item));
        if (value instanceof Object) {
            const cloned = {};
            for (const key in value) {
                if (value.hasOwnProperty(key)) {
                    cloned[key] = this._deepClone(value[key]);
                }
            }
            return cloned;
        }
        return value;
    }
};

// Ajouter un helper pour créer des watchers de formulaire
window.formWatcherMixin = {
    /**
     * Initialiser les watchers pour un formulaire complet
     * @param {Object} formConfig - Configuration du formulaire
     */
    initFormWatchers(formConfig) {
        const {
            fields,
            sessionKey,
            onFieldChange = null,
            validateField = null,
            debounce = 300
        } = formConfig;
        
        // Créer un watcher pour chaque champ
        Object.entries(fields).forEach(([fieldName, fieldConfig]) => {
            const {
                watch = true,
                transform = null,
                validate = null,
                immediate = false
            } = fieldConfig;
            
            if (!watch) return;
            
            this.watchOptimized(fieldName, (newValue, oldValue) => {
                // Validation si fournie
                if (validate || validateField) {
                    const validator = validate || validateField;
                    const validation = validator(fieldName, newValue);
                    if (!validation.valid) {
                        // Gérer l'erreur de validation
                        if (this.setFieldError) {
                            this.setFieldError(fieldName, validation.error);
                        }
                        return;
                    }
                }
                
                // Transformation si fournie
                const valueToSave = transform ? transform(newValue) : newValue;
                
                // Callback personnalisé
                if (onFieldChange) {
                    onFieldChange(fieldName, valueToSave, oldValue);
                }
                
                // Sauvegarder dans la session
                const data = {};
                data[`${sessionKey}_${fieldName}`] = valueToSave;
                
                if (this.saveToSession) {
                    this.saveToSession(data);
                } else if (window.session) {
                    window.session.patch(data);
                }
            }, { debounce, immediate });
        });
    }
};