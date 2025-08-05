/**
 * Service de mémoization pour optimiser les calculs coûteux
 * Évite de recalculer les mêmes valeurs plusieurs fois
 */
window.memoizationService = {
    // Cache pour stocker les résultats
    _cache: new Map(),
    
    // Statistiques pour monitoring
    _stats: {
        hits: 0,
        misses: 0,
        evictions: 0
    },
    
    // Configuration
    MAX_CACHE_SIZE: 1000,
    DEFAULT_TTL: 5 * 60 * 1000, // 5 minutes
    
    /**
     * Mémoize une fonction pure
     * @param {Function} fn - Fonction à mémoizer
     * @param {Object} options - Options de mémoization
     * @returns {Function} Fonction mémoizée
     */
    memoize(fn, options = {}) {
        const {
            keyGenerator = this._defaultKeyGenerator,
            ttl = this.DEFAULT_TTL,
            maxSize = 100,
            name = fn.name || 'anonymous'
        } = options;
        
        // Créer un cache dédié pour cette fonction
        const fnCache = new Map();
        const cacheKey = `fn_${name}`;
        
        return (...args) => {
            // Générer la clé de cache
            const key = keyGenerator(...args);
            const fullKey = `${cacheKey}_${key}`;
            
            // Vérifier le cache
            const cached = this._getFromCache(fnCache, fullKey);
            if (cached !== undefined) {
                this._stats.hits++;
                return cached;
            }
            
            // Calculer la valeur
            this._stats.misses++;
            const result = fn(...args);
            
            // Mettre en cache avec TTL
            this._setInCache(fnCache, fullKey, result, ttl, maxSize);
            
            return result;
        };
    },
    
    /**
     * Mémoize une méthode de composant Alpine
     * @param {Object} component - Composant Alpine
     * @param {string} methodName - Nom de la méthode
     * @param {Object} options - Options de mémoization
     */
    memoizeMethod(component, methodName, options = {}) {
        const originalMethod = component[methodName];
        if (typeof originalMethod !== 'function') {
            throw new Error(`${methodName} n'est pas une méthode`);
        }
        
        component[methodName] = this.memoize(originalMethod.bind(component), {
            ...options,
            name: `${component.constructor.name || 'Component'}.${methodName}`
        });
    },
    
    /**
     * Créer un calculateur mémoizé pour les valeurs dérivées
     * @param {Function} calculator - Fonction de calcul
     * @param {Array<string>} dependencies - Propriétés dont dépend le calcul
     * @param {Object} options - Options
     * @returns {Function} Getter mémoizé
     */
    createComputedMemo(calculator, dependencies, options = {}) {
        const {
            ttl = 1000, // TTL court pour les computed
            name = 'computed'
        } = options;
        
        let lastDeps = null;
        let lastResult = null;
        let lastTime = 0;
        
        return function() {
            const now = Date.now();
            const currentDeps = dependencies.map(dep => this[dep]);
            
            // Vérifier si les dépendances ont changé ou si le TTL est expiré
            if (lastDeps && now - lastTime < ttl && this._arrayEquals(currentDeps, lastDeps)) {
                return lastResult;
            }
            
            // Recalculer
            lastDeps = [...currentDeps];
            lastResult = calculator.apply(this, currentDeps);
            lastTime = now;
            
            return lastResult;
        };
    },
    
    /**
     * Mémoize spécifiquement pour les calculs de KPI
     * @param {string} kpiType - Type de KPI
     * @param {Function} calculator - Fonction de calcul
     * @returns {Function} Fonction mémoizée
     */
    memoizeKPI(kpiType, calculator) {
        return this.memoize(calculator, {
            name: `kpi_${kpiType}`,
            ttl: 10000, // 10 secondes pour les KPI
            keyGenerator: (...args) => {
                // Générer une clé basée sur les données significatives
                return JSON.stringify(args.map(arg => {
                    if (typeof arg === 'object' && arg !== null) {
                        // Extraire les propriétés importantes
                        return {
                            totalLength: arg.totalLength,
                            okLength: arg.okLength,
                            targetSpeed: arg.targetSpeed,
                            totalMinutes: arg.totalMinutes,
                            downtimeMinutes: arg.downtimeMinutes
                        };
                    }
                    return arg;
                }));
            }
        });
    },
    
    /**
     * Invalider le cache pour une fonction ou globalement
     * @param {string} functionName - Nom de la fonction (optionnel)
     */
    invalidate(functionName = null) {
        if (functionName) {
            const cacheKey = `fn_${functionName}`;
            let count = 0;
            
            for (const [key] of this._cache) {
                if (key.startsWith(cacheKey)) {
                    this._cache.delete(key);
                    count++;
                }
            }
            
            debug(`Cache invalidé pour ${functionName}: ${count} entrées supprimées`);
        } else {
            const size = this._cache.size;
            this._cache.clear();
            debug(`Cache global invalidé: ${size} entrées supprimées`);
        }
    },
    
    /**
     * Invalider le cache quand certaines données changent
     * @param {Array<string>} patterns - Patterns de clés à invalider
     */
    invalidatePatterns(patterns) {
        let count = 0;
        
        for (const [key] of this._cache) {
            if (patterns.some(pattern => key.includes(pattern))) {
                this._cache.delete(key);
                count++;
            }
        }
        
        if (count > 0) {
            debug(`Cache invalidé: ${count} entrées correspondant aux patterns`);
        }
    },
    
    /**
     * Obtenir les statistiques du cache
     * @returns {Object} Statistiques
     */
    getStats() {
        const hitRate = this._stats.hits + this._stats.misses > 0
            ? (this._stats.hits / (this._stats.hits + this._stats.misses) * 100).toFixed(2)
            : 0;
            
        return {
            ...this._stats,
            hitRate: `${hitRate}%`,
            cacheSize: this._cache.size,
            maxSize: this.MAX_CACHE_SIZE
        };
    },
    
    /**
     * Nettoyer les entrées expirées
     */
    cleanup() {
        const now = Date.now();
        let cleaned = 0;
        
        for (const [key, entry] of this._cache) {
            if (entry.expiry && entry.expiry < now) {
                this._cache.delete(key);
                cleaned++;
            }
        }
        
        if (cleaned > 0) {
            this._stats.evictions += cleaned;
            debug(`Cache cleanup: ${cleaned} entrées expirées supprimées`);
        }
    },
    
    // Méthodes privées
    _getFromCache(cache, key) {
        const entry = cache.get(key) || this._cache.get(key);
        
        if (!entry) return undefined;
        
        // Vérifier l'expiration
        if (entry.expiry && entry.expiry < Date.now()) {
            cache.delete(key);
            this._cache.delete(key);
            return undefined;
        }
        
        return entry.value;
    },
    
    _setInCache(cache, key, value, ttl, maxSize) {
        const entry = {
            value,
            expiry: ttl ? Date.now() + ttl : null
        };
        
        // Vérifier la taille du cache local
        if (cache.size >= maxSize) {
            // Supprimer la plus ancienne entrée (FIFO)
            const firstKey = cache.keys().next().value;
            cache.delete(firstKey);
            this._stats.evictions++;
        }
        
        // Vérifier la taille du cache global
        if (this._cache.size >= this.MAX_CACHE_SIZE) {
            const firstKey = this._cache.keys().next().value;
            this._cache.delete(firstKey);
            this._stats.evictions++;
        }
        
        // Ajouter aux deux caches
        cache.set(key, entry);
        this._cache.set(key, entry);
    },
    
    _defaultKeyGenerator(...args) {
        return JSON.stringify(args);
    },
    
    _arrayEquals(a, b) {
        if (a.length !== b.length) return false;
        return a.every((val, i) => val === b[i]);
    }
};

// Créer un mixin pour Alpine.js
window.memoizationMixin = {
    initMemoization() {
        // Nettoyer périodiquement
        this._cleanupInterval = setInterval(() => {
            window.memoizationService.cleanup();
        }, 60000); // Toutes les minutes
    },
    
    destroyMemoization() {
        if (this._cleanupInterval) {
            clearInterval(this._cleanupInterval);
        }
    },
    
    /**
     * Helper pour créer un getter mémoizé
     */
    memoizedGetter(name, calculator, dependencies) {
        Object.defineProperty(this, name, {
            get: window.memoizationService.createComputedMemo(
                calculator,
                dependencies,
                { name }
            )
        });
    }
};

// Auto-cleanup au déchargement de la page
window.addEventListener('beforeunload', () => {
    window.memoizationService.cleanup();
});

// Exposer des helpers pratiques
window.memoize = (fn, options) => window.memoizationService.memoize(fn, options);
window.memoizeKPI = (type, fn) => window.memoizationService.memoizeKPI(type, fn);