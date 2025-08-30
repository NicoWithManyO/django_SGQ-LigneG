/**
 * Service de cache local avec synchronisation différée
 * Optimise les performances en réduisant les appels API
 */
window.cacheService = {
    // Configuration
    SYNC_INTERVAL: 3000, // 3 secondes
    MAX_RETRIES: 3,
    
    // État interne
    _cache: new Map(),
    _pendingSync: new Map(),
    _syncInterval: null,
    _retryCount: 0,
    _isOnline: true,
    
    /**
     * Initialiser le service
     */
    init() {
        debug('Cache service initialized');
        
        // Démarrer la synchronisation périodique
        this._syncInterval = setInterval(() => this.syncToServer(), this.SYNC_INTERVAL);
        
        // Écouter les changements de connectivité
        window.addEventListener('online', () => {
            this._isOnline = true;
            this.syncToServer(); // Sync immédiate au retour en ligne
        });
        
        window.addEventListener('offline', () => {
            this._isOnline = false;
        });
        
        // Synchroniser avant de quitter la page
        window.addEventListener('beforeunload', () => {
            this.forceSyncNow();
        });
    },
    
    /**
     * Arrêter le service
     */
    destroy() {
        if (this._syncInterval) {
            clearInterval(this._syncInterval);
            this._syncInterval = null;
        }
        this.forceSyncNow();
    },
    
    /**
     * Définir une valeur dans le cache
     */
    set(key, value) {
        this._cache.set(key, value);
        this._pendingSync.set(key, value);
        
        // Si critique, forcer la sync
        if (this._isCriticalData(key)) {
            this.syncToServer();
        }
    },
    
    /**
     * Définir plusieurs valeurs
     */
    patch(data) {
        Object.entries(data).forEach(([key, value]) => {
            this._cache.set(key, value);
            this._pendingSync.set(key, value);
        });
    },
    
    /**
     * Récupérer une valeur du cache
     */
    get(key) {
        return this._cache.get(key);
    },
    
    /**
     * Récupérer toutes les données
     */
    getAll() {
        return Object.fromEntries(this._cache);
    },
    
    /**
     * Synchroniser avec le serveur
     */
    async syncToServer() {
        // Pas de sync si offline ou rien à synchroniser
        if (!this._isOnline || this._pendingSync.size === 0) {
            return;
        }
        
        // Copier les données à synchroniser
        const dataToSync = Object.fromEntries(this._pendingSync);
        const keysToSync = Array.from(this._pendingSync.keys());
        
        debug(`Syncing ${keysToSync.length} items to server`);
        
        try {
            // Utiliser la session API existante
            if (window.session && window.session.patch) {
                await window.session.patch(dataToSync);
                
                // Succès : vider les données synchronisées
                keysToSync.forEach(key => this._pendingSync.delete(key));
                this._retryCount = 0;
                
                debug('Sync successful');
            }
        } catch (error) {
            debug('Sync failed:', error);
            
            // En cas d'erreur, réessayer plus tard
            this._retryCount++;
            if (this._retryCount >= this.MAX_RETRIES) {
                showNotification('error', 'Erreur de synchronisation des données');
                this._retryCount = 0;
            }
        }
    },
    
    /**
     * Forcer la synchronisation immédiate
     */
    forceSyncNow() {
        // Synchrone pour beforeunload
        if (this._pendingSync.size === 0) return;
        
        const dataToSync = Object.fromEntries(this._pendingSync);
        
        // Utiliser sendBeacon si disponible (plus fiable pour beforeunload)
        if (navigator.sendBeacon && window.session) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const blob = new Blob([JSON.stringify(dataToSync)], { type: 'application/json' });
            
            navigator.sendBeacon('/api/session/', blob);
        } else {
            // Fallback sur XMLHttpRequest synchrone
            const xhr = new XMLHttpRequest();
            xhr.open('PATCH', '/api/session/', false); // false = synchrone
            xhr.setRequestHeader('Content-Type', 'application/json');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
            xhr.send(JSON.stringify(dataToSync));
        }
    },
    
    /**
     * Vérifier si une donnée est critique (doit être synchronisée immédiatement)
     */
    _isCriticalData(key) {
        const criticalKeys = [
            'shift_saved',
            'roll_saved',
            'quality_control_validated'
        ];
        return criticalKeys.some(k => key.includes(k));
    },
    
    /**
     * Obtenir des statistiques du cache
     */
    getStats() {
        return {
            cacheSize: this._cache.size,
            pendingSync: this._pendingSync.size,
            isOnline: this._isOnline,
            retryCount: this._retryCount
        };
    }
};

// Démarrer automatiquement
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.cacheService.init());
} else {
    window.cacheService.init();
}