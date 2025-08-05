/**
 * Service centralisé de validation
 * Évite la duplication de code de validation dans les composants
 */
window.validationService = {
    /**
     * Nettoyer et parser une valeur numérique
     * @param {string} value - Valeur à nettoyer
     * @returns {string} Valeur nettoyée
     */
    parseNumeric(value) {
        if (!value) return '';
        return value.toString()
            .replace(/[^0-9.,\-]/g, '')  // Garder chiffres, virgule, point, moins
            .replace(',', '.');          // Virgule → point
    },
    
    /**
     * Valider une entrée numérique en temps réel
     * @param {Event} event - Événement clavier
     * @param {Object} options - Options de validation
     * @returns {boolean} true si valide
     */
    validateNumericInput(event, options = {}) {
        const {
            allowNegative = false,
            allowDecimal = true,
            maxDecimals = 2,
            min = null,
            max = null
        } = options;
        
        // Touches spéciales toujours autorisées
        const specialKeys = ['Backspace', 'Delete', 'Tab', 'Enter', 'ArrowLeft', 'ArrowRight'];
        if (specialKeys.includes(event.key)) return true;
        
        // Ctrl+A, Ctrl+C, Ctrl+V
        if (event.ctrlKey || event.metaKey) return true;
        
        const char = event.key;
        const currentValue = event.target.value;
        const cursorPos = event.target.selectionStart;
        
        // Vérifier le caractère
        if (!/[0-9,.\-]/.test(char)) {
            event.preventDefault();
            return false;
        }
        
        // Gérer le signe moins
        if (char === '-') {
            if (!allowNegative || cursorPos !== 0 || currentValue.includes('-')) {
                event.preventDefault();
                return false;
            }
        }
        
        // Gérer virgule/point
        if (char === ',' || char === '.') {
            if (!allowDecimal || /[,.]/.test(currentValue)) {
                event.preventDefault();
                return false;
            }
            
            // Vérifier le nombre de décimales après
            const afterDot = currentValue.substring(currentValue.indexOf('.') + 1);
            if (afterDot.length >= maxDecimals) {
                event.preventDefault();
                return false;
            }
        }
        
        // Simuler la nouvelle valeur pour validation min/max
        if (min !== null || max !== null) {
            const newValue = currentValue.slice(0, cursorPos) + char + currentValue.slice(cursorPos);
            const numValue = parseFloat(newValue.replace(',', '.'));
            
            if (!isNaN(numValue)) {
                if (min !== null && numValue < min) {
                    event.preventDefault();
                    return false;
                }
                if (max !== null && numValue > max) {
                    event.preventDefault();
                    return false;
                }
            }
        }
        
        return true;
    },
    
    /**
     * Formater une valeur numérique pour l'affichage
     * @param {number|string} value - Valeur à formater
     * @param {Object} options - Options de formatage
     * @returns {string} Valeur formatée
     */
    formatNumeric(value, options = {}) {
        const {
            decimals = 2,
            thousandsSeparator = ' ',
            decimalSeparator = ',',
            unit = '',
            defaultValue = '--'
        } = options;
        
        if (value === null || value === undefined || value === '') {
            return defaultValue;
        }
        
        const num = parseFloat(value);
        if (isNaN(num)) return defaultValue;
        
        // Formater avec le bon nombre de décimales
        let formatted = num.toFixed(decimals);
        
        // Séparer partie entière et décimale
        let [integerPart, decimalPart] = formatted.split('.');
        
        // Ajouter séparateurs de milliers
        if (thousandsSeparator) {
            integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
        }
        
        // Reconstruire avec le bon séparateur décimal
        formatted = integerPart;
        if (decimalPart) {
            formatted += decimalSeparator + decimalPart;
        }
        
        // Ajouter l'unité
        if (unit) {
            formatted += ' ' + unit;
        }
        
        return formatted;
    },
    
    /**
     * Valider un champ selon des règles
     * @param {any} value - Valeur à valider
     * @param {Object} rules - Règles de validation
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate(value, rules = {}) {
        const errors = [];
        
        // Requis
        if (rules.required && !value) {
            errors.push('Ce champ est requis');
        }
        
        // Type numérique
        if (rules.numeric && value) {
            const num = parseFloat(this.parseNumeric(value));
            if (isNaN(num)) {
                errors.push('Valeur numérique invalide');
            } else {
                // Min/Max
                if (rules.min !== undefined && num < rules.min) {
                    errors.push(`Valeur minimale : ${rules.min}`);
                }
                if (rules.max !== undefined && num > rules.max) {
                    errors.push(`Valeur maximale : ${rules.max}`);
                }
            }
        }
        
        // Pattern regex
        if (rules.pattern && value && !rules.pattern.test(value)) {
            errors.push(rules.patternMessage || 'Format invalide');
        }
        
        // Longueur
        if (rules.minLength && value && value.length < rules.minLength) {
            errors.push(`Minimum ${rules.minLength} caractères`);
        }
        if (rules.maxLength && value && value.length > rules.maxLength) {
            errors.push(`Maximum ${rules.maxLength} caractères`);
        }
        
        // Validation custom
        if (rules.custom && typeof rules.custom === 'function') {
            const customError = rules.custom(value);
            if (customError) {
                errors.push(customError);
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    },
    
    /**
     * Valider un formulaire complet
     * @param {Object} data - Données du formulaire
     * @param {Object} schema - Schéma de validation
     * @returns {Object} { valid: boolean, errors: Object }
     */
    validateForm(data, schema) {
        const errors = {};
        let isValid = true;
        
        Object.entries(schema).forEach(([field, rules]) => {
            const value = data[field];
            const result = this.validate(value, rules);
            
            if (!result.valid) {
                errors[field] = result.errors;
                isValid = false;
            }
        });
        
        return { valid: isValid, errors };
    },
    
    /**
     * Créer un validateur pour Alpine.js
     * @param {Object} schema - Schéma de validation
     * @returns {Object} Objet Alpine avec méthodes de validation
     */
    createAlpineValidator(schema) {
        return {
            errors: {},
            touched: {},
            
            validateField(field, value) {
                if (!schema[field]) return true;
                
                const result = validationService.validate(value, schema[field]);
                if (result.valid) {
                    delete this.errors[field];
                } else {
                    this.errors[field] = result.errors;
                }
                
                return result.valid;
            },
            
            touchField(field) {
                this.touched[field] = true;
            },
            
            hasError(field) {
                return this.touched[field] && this.errors[field] && this.errors[field].length > 0;
            },
            
            getError(field) {
                return this.hasError(field) ? this.errors[field][0] : '';
            },
            
            validateAll(data) {
                const result = validationService.validateForm(data, schema);
                this.errors = result.errors;
                
                // Marquer tous les champs comme touchés
                Object.keys(schema).forEach(field => {
                    this.touched[field] = true;
                });
                
                return result.valid;
            },
            
            reset() {
                this.errors = {};
                this.touched = {};
            }
        };
    }
};

// Exporter pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = validationService;
}