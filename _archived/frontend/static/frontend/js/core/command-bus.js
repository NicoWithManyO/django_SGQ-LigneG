/**
 * CommandBus - Gestionnaire de commandes pour encapsuler la logique métier
 * 
 * Centralise l'exécution des actions métier avec validation et effets secondaires
 */
class CommandBus {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.handlers = new Map();
        this.validators = new Map();
        this.effects = new Map();
        this.interceptors = [];
        this.executionLog = [];
        this.maxLog = 100;
    }
    
    /**
     * Enregistrer un handler de commande
     * @param {string} command - Nom de la commande
     * @param {Function} handler - Fonction qui exécute la commande
     * @param {Function} validator - Fonction de validation (optionnel)
     * @param {Array} effects - Effets secondaires (optionnel)
     */
    register(command, handler, validator = null, effects = []) {
        if (!command || typeof handler !== 'function') {
            throw new Error('Command name and handler function are required');
        }
        
        this.handlers.set(command, handler);
        
        if (validator && typeof validator === 'function') {
            this.validators.set(command, validator);
        }
        
        if (effects && Array.isArray(effects)) {
            this.effects.set(command, effects);
        }
    }
    
    /**
     * Exécuter une commande
     * @param {string} command - Nom de la commande
     * @param {Object} payload - Données de la commande
     * @returns {Promise} Résultat de l'exécution
     */
    async execute(command, payload = {}) {
        const startTime = Date.now();
        const executionId = this._generateId();
        
        // Log de début
        const logEntry = {
            id: executionId,
            command,
            payload: this._sanitizeForLog(payload),
            startTime,
            status: 'pending'
        };
        
        this._addToLog(logEntry);
        
        try {
            // Vérifier que le handler existe
            const handler = this.handlers.get(command);
            if (!handler) {
                throw new Error(`No handler registered for command: ${command}`);
            }
            
            // Intercepteurs avant exécution
            for (const interceptor of this.interceptors) {
                if (interceptor.before) {
                    await interceptor.before(command, payload);
                }
            }
            
            // Validation
            const validator = this.validators.get(command);
            if (validator) {
                const validation = await validator(payload);
                if (!validation.valid) {
                    const error = new ValidationError(validation.errors || ['Validation failed']);
                    error.validation = validation;
                    throw error;
                }
            }
            
            // Exécution de la commande
            if (window.DEBUG) {
                console.log(`🚀 Executing command: ${command}`, payload);
            }
            
            const result = await handler(payload, this.stateManager);
            
            // Effets secondaires
            const effects = this.effects.get(command) || [];
            const effectResults = [];
            
            for (const effect of effects) {
                try {
                    const effectResult = await effect(result, payload, this.stateManager);
                    effectResults.push({ success: true, result: effectResult });
                } catch (effectError) {
                    console.error(`Effect error in ${command}:`, effectError);
                    effectResults.push({ success: false, error: effectError });
                }
            }
            
            // Intercepteurs après exécution
            for (const interceptor of this.interceptors) {
                if (interceptor.after) {
                    await interceptor.after(command, payload, result);
                }
            }
            
            // Mise à jour du log
            logEntry.endTime = Date.now();
            logEntry.duration = logEntry.endTime - startTime;
            logEntry.status = 'success';
            logEntry.result = this._sanitizeForLog(result);
            logEntry.effectResults = effectResults;
            
            if (window.DEBUG) {
                console.log(`✅ Command completed: ${command} (${logEntry.duration}ms)`);
            }
            
            return result;
            
        } catch (error) {
            // Intercepteurs en cas d'erreur
            for (const interceptor of this.interceptors) {
                if (interceptor.error) {
                    await interceptor.error(command, payload, error);
                }
            }
            
            // Mise à jour du log
            logEntry.endTime = Date.now();
            logEntry.duration = logEntry.endTime - startTime;
            logEntry.status = 'error';
            logEntry.error = {
                message: error.message,
                type: error.constructor.name,
                validation: error.validation
            };
            
            console.error(`❌ Command failed: ${command}`, error);
            
            throw error;
        }
    }
    
    /**
     * Exécuter plusieurs commandes en séquence
     * @param {Array} commands - Liste de {command, payload}
     */
    async executeSequence(commands) {
        const results = [];
        
        for (const { command, payload } of commands) {
            try {
                const result = await this.execute(command, payload);
                results.push({ command, success: true, result });
            } catch (error) {
                results.push({ command, success: false, error });
                // Arrêter la séquence en cas d'erreur
                break;
            }
        }
        
        return results;
    }
    
    /**
     * Exécuter plusieurs commandes en parallèle
     * @param {Array} commands - Liste de {command, payload}
     */
    async executeParallel(commands) {
        const promises = commands.map(({ command, payload }) => 
            this.execute(command, payload)
                .then(result => ({ command, success: true, result }))
                .catch(error => ({ command, success: false, error }))
        );
        
        return Promise.all(promises);
    }
    
    /**
     * Ajouter un intercepteur global
     * @param {Object} interceptor - {before, after, error}
     */
    addInterceptor(interceptor) {
        if (typeof interceptor === 'object') {
            this.interceptors.push(interceptor);
        }
    }
    
    /**
     * Vérifier si une commande existe
     * @param {string} command - Nom de la commande
     */
    hasCommand(command) {
        return this.handlers.has(command);
    }
    
    /**
     * Obtenir la liste des commandes enregistrées
     */
    getCommands() {
        return Array.from(this.handlers.keys());
    }
    
    /**
     * Obtenir l'historique d'exécution
     * @param {Object} filter - Filtres optionnels
     */
    getExecutionLog(filter = {}) {
        let log = [...this.executionLog];
        
        if (filter.command) {
            log = log.filter(l => l.command === filter.command);
        }
        
        if (filter.status) {
            log = log.filter(l => l.status === filter.status);
        }
        
        if (filter.since) {
            log = log.filter(l => l.startTime > filter.since);
        }
        
        return log;
    }
    
    // Méthodes privées
    
    _addToLog(entry) {
        this.executionLog.push(entry);
        if (this.executionLog.length > this.maxLog) {
            this.executionLog.shift();
        }
    }
    
    _sanitizeForLog(data) {
        // Retirer les données sensibles du log
        if (!data || typeof data !== 'object') return data;
        
        const sanitized = {};
        for (const key in data) {
            if (key.toLowerCase().includes('password') || 
                key.toLowerCase().includes('token') ||
                key.toLowerCase().includes('secret')) {
                sanitized[key] = '[REDACTED]';
            } else if (typeof data[key] === 'object') {
                sanitized[key] = this._sanitizeForLog(data[key]);
            } else {
                sanitized[key] = data[key];
            }
        }
        
        return sanitized;
    }
    
    _generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

/**
 * Erreur de validation personnalisée
 */
class ValidationError extends Error {
    constructor(errors) {
        super('Validation failed');
        this.name = 'ValidationError';
        this.errors = errors;
    }
}

// Créer l'instance globale
window.commandBus = new CommandBus(window.stateManager);

// Intercepteur de logging en développement
if (window.DEBUG) {
    window.commandBus.addInterceptor({
        before: (command, payload) => {
            console.group(`Command: ${command}`);
            console.log('Payload:', payload);
        },
        after: (command, payload, result) => {
            console.log('Result:', result);
            console.groupEnd();
        },
        error: (command, payload, error) => {
            console.error('Error:', error);
            console.groupEnd();
        }
    });
}

// Exposer pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CommandBus, ValidationError };
}