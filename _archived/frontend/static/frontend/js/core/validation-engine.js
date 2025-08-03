/**
 * ValidationEngine - Moteur de validation multi-niveaux
 * 
 * Gère la validation des données avec règles prédéfinies et personnalisées
 */
class ValidationEngine {
    constructor() {
        this.rules = new Map();
        this.customValidators = new Map();
        this.validationCache = new Map();
        this.cacheTimeout = 5000; // 5 secondes
    }
    
    /**
     * Définir des règles de validation pour un chemin
     * @param {string} path - Chemin de la propriété
     * @param {Array} rules - Liste des règles
     */
    defineRules(path, rules) {
        if (!Array.isArray(rules)) {
            throw new Error('Rules must be an array');
        }
        
        this.rules.set(path, rules);
        
        // Invalider le cache pour ce chemin
        this._clearCache(path);
        
        // Commenté pour éviter la pollution de la console
        // if (window.DEBUG) {
        //     console.log(`📋 Validation rules defined for: ${path}`);
        // }
    }
    
    /**
     * Enregistrer un validateur personnalisé
     * @param {string} name - Nom du validateur
     * @param {Function} validator - Fonction de validation
     */
    registerValidator(name, validator) {
        if (typeof validator !== 'function') {
            throw new Error('Validator must be a function');
        }
        
        this.customValidators.set(name, validator);
    }
    
    /**
     * Valider une valeur selon les règles définies
     * @param {string} path - Chemin de la propriété
     * @param {*} value - Valeur à valider
     * @param {Object} context - Contexte de validation
     * @returns {Object} Résultat de validation
     */
    validate(path, value, context = {}) {
        // Vérifier le cache
        const cacheKey = this._getCacheKey(path, value, context);
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;
        
        const rules = this.rules.get(path) || [];
        const errors = [];
        const warnings = [];
        let valid = true;
        
        for (const rule of rules) {
            // Vérifier si la règle s'applique
            if (rule.when && !rule.when(context)) {
                continue;
            }
            
            const result = this._executeRule(rule, value, context);
            
            if (!result.valid) {
                valid = false;
                if (result.error) {
                    errors.push({
                        rule: rule.type,
                        message: result.error,
                        severity: result.severity || 'error'
                    });
                }
            }
            
            if (result.warning) {
                warnings.push({
                    rule: rule.type,
                    message: result.warning,
                    severity: result.severity || 'warning'
                });
            }
        }
        
        const validationResult = {
            valid,
            errors,
            warnings,
            path,
            value,
            timestamp: Date.now()
        };
        
        // Mettre en cache
        this._setCache(cacheKey, validationResult);
        
        return validationResult;
    }
    
    /**
     * Valider plusieurs champs en une fois
     * @param {Object} data - Objet avec chemins et valeurs
     * @param {Object} context - Contexte global
     */
    validateMultiple(data, context = {}) {
        const results = {};
        let allValid = true;
        const allErrors = [];
        const allWarnings = [];
        
        for (const [path, value] of Object.entries(data)) {
            const result = this.validate(path, value, context);
            results[path] = result;
            
            if (!result.valid) {
                allValid = false;
                allErrors.push(...result.errors.map(e => ({ ...e, path })));
            }
            
            if (result.warnings.length > 0) {
                allWarnings.push(...result.warnings.map(w => ({ ...w, path })));
            }
        }
        
        return {
            valid: allValid,
            results,
            errors: allErrors,
            warnings: allWarnings
        };
    }
    
    /**
     * Valider avec dépendances (validation croisée)
     * @param {Object} data - Toutes les données
     * @param {Array} dependencies - Règles de dépendance
     */
    validateWithDependencies(data, dependencies) {
        const results = this.validateMultiple(data);
        
        // Appliquer les règles de dépendance
        for (const dep of dependencies) {
            const depResult = this._validateDependency(dep, data);
            if (!depResult.valid) {
                results.valid = false;
                results.errors.push({
                    rule: 'dependency',
                    message: depResult.error,
                    paths: dep.paths
                });
            }
        }
        
        return results;
    }
    
    // Règles prédéfinies
    
    _executeRule(rule, value, context) {
        switch (rule.type) {
            case 'required':
                return this._validateRequired(value, rule);
                
            case 'numeric':
                return this._validateNumeric(value, rule);
                
            case 'range':
                return this._validateRange(value, rule);
                
            case 'length':
                return this._validateLength(value, rule);
                
            case 'pattern':
                return this._validatePattern(value, rule);
                
            case 'date':
                return this._validateDate(value, rule);
                
            case 'time':
                return this._validateTime(value, rule);
                
            case 'custom':
                return this._validateCustom(value, rule, context);
                
            default:
                console.warn(`Unknown validation rule type: ${rule.type}`);
                return { valid: true };
        }
    }
    
    _validateRequired(value, rule) {
        const isEmpty = value === null || value === undefined || 
                       value === '' || (Array.isArray(value) && value.length === 0);
        
        if (isEmpty) {
            return {
                valid: false,
                error: rule.message || 'Ce champ est requis'
            };
        }
        
        return { valid: true };
    }
    
    _validateNumeric(value, rule) {
        if (value === null || value === undefined || value === '') {
            return { valid: true }; // Utiliser 'required' pour rendre obligatoire
        }
        
        const num = typeof value === 'string' ? parseFloat(value.replace(',', '.')) : value;
        
        if (isNaN(num)) {
            return {
                valid: false,
                error: rule.message || 'Valeur numérique requise'
            };
        }
        
        return { valid: true };
    }
    
    _validateRange(value, rule) {
        if (value === null || value === undefined || value === '') {
            return { valid: true };
        }
        
        const num = typeof value === 'string' ? parseFloat(value.replace(',', '.')) : value;
        
        if (isNaN(num)) {
            return {
                valid: false,
                error: 'Valeur numérique requise'
            };
        }
        
        if (rule.min !== undefined && num < rule.min) {
            return {
                valid: false,
                error: rule.message || `La valeur doit être supérieure ou égale à ${rule.min}`
            };
        }
        
        if (rule.max !== undefined && num > rule.max) {
            return {
                valid: false,
                error: rule.message || `La valeur doit être inférieure ou égale à ${rule.max}`
            };
        }
        
        // Alertes pour les seuils
        if (rule.minAlert !== undefined && num < rule.minAlert) {
            return {
                valid: true,
                warning: rule.alertMessage || `Valeur en dessous du seuil d'alerte (${rule.minAlert})`,
                severity: 'warning'
            };
        }
        
        if (rule.maxAlert !== undefined && num > rule.maxAlert) {
            return {
                valid: true,
                warning: rule.alertMessage || `Valeur au-dessus du seuil d'alerte (${rule.maxAlert})`,
                severity: 'warning'
            };
        }
        
        return { valid: true };
    }
    
    _validateLength(value, rule) {
        if (value === null || value === undefined) {
            return { valid: true };
        }
        
        const str = String(value);
        const len = str.length;
        
        if (rule.min !== undefined && len < rule.min) {
            return {
                valid: false,
                error: rule.message || `Minimum ${rule.min} caractères requis`
            };
        }
        
        if (rule.max !== undefined && len > rule.max) {
            return {
                valid: false,
                error: rule.message || `Maximum ${rule.max} caractères autorisés`
            };
        }
        
        if (rule.exact !== undefined && len !== rule.exact) {
            return {
                valid: false,
                error: rule.message || `Exactement ${rule.exact} caractères requis`
            };
        }
        
        return { valid: true };
    }
    
    _validatePattern(value, rule) {
        if (value === null || value === undefined || value === '') {
            return { valid: true };
        }
        
        const pattern = rule.pattern instanceof RegExp ? rule.pattern : new RegExp(rule.pattern);
        
        if (!pattern.test(String(value))) {
            return {
                valid: false,
                error: rule.message || 'Format invalide'
            };
        }
        
        return { valid: true };
    }
    
    _validateDate(value, rule) {
        if (!value) return { valid: true };
        
        const date = new Date(value);
        
        if (isNaN(date.getTime())) {
            return {
                valid: false,
                error: rule.message || 'Date invalide'
            };
        }
        
        const now = new Date();
        
        if (rule.min) {
            const minDate = rule.min === 'today' ? new Date(now.toDateString()) : new Date(rule.min);
            if (date < minDate) {
                return {
                    valid: false,
                    error: rule.message || `La date doit être après le ${minDate.toLocaleDateString('fr-FR')}`
                };
            }
        }
        
        if (rule.max) {
            const maxDate = rule.max === 'today' ? new Date(now.toDateString()) : new Date(rule.max);
            if (date > maxDate) {
                return {
                    valid: false,
                    error: rule.message || `La date doit être avant le ${maxDate.toLocaleDateString('fr-FR')}`
                };
            }
        }
        
        return { valid: true };
    }
    
    _validateTime(value, rule) {
        if (!value) return { valid: true };
        
        const timePattern = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        
        if (!timePattern.test(value)) {
            return {
                valid: false,
                error: rule.message || 'Format d\'heure invalide (HH:MM)'
            };
        }
        
        return { valid: true };
    }
    
    _validateCustom(value, rule, context) {
        const validator = this.customValidators.get(rule.validator);
        
        if (!validator) {
            console.error(`Custom validator not found: ${rule.validator}`);
            return { valid: true };
        }
        
        try {
            const result = validator(value, context, rule);
            
            // Normaliser le résultat
            if (typeof result === 'boolean') {
                return { valid: result, error: result ? null : rule.message };
            }
            
            return result;
        } catch (error) {
            console.error(`Custom validator error: ${rule.validator}`, error);
            return {
                valid: false,
                error: 'Erreur de validation'
            };
        }
    }
    
    _validateDependency(dependency, data) {
        try {
            const result = dependency.validate(data);
            
            if (typeof result === 'boolean') {
                return {
                    valid: result,
                    error: result ? null : dependency.message || 'Validation de dépendance échouée'
                };
            }
            
            return result;
        } catch (error) {
            console.error('Dependency validation error:', error);
            return {
                valid: false,
                error: 'Erreur de validation de dépendance'
            };
        }
    }
    
    // Gestion du cache
    
    _getCacheKey(path, value, context) {
        return JSON.stringify({ path, value, context });
    }
    
    _getFromCache(key) {
        const cached = this.validationCache.get(key);
        
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached;
        }
        
        return null;
    }
    
    _setCache(key, result) {
        this.validationCache.set(key, result);
        
        // Nettoyer le cache périodiquement
        if (this.validationCache.size > 1000) {
            this._cleanCache();
        }
    }
    
    _clearCache(path) {
        // Supprimer toutes les entrées liées à ce chemin
        for (const [key] of this.validationCache) {
            if (key.includes(`"path":"${path}"`)) {
                this.validationCache.delete(key);
            }
        }
    }
    
    _cleanCache() {
        const now = Date.now();
        
        for (const [key, value] of this.validationCache) {
            if (now - value.timestamp > this.cacheTimeout) {
                this.validationCache.delete(key);
            }
        }
    }
}

// Créer l'instance globale
window.validationEngine = new ValidationEngine();

// Exposer pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ValidationEngine;
}