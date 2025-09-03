/**
 * Service de validation WCM
 * Gère la validation des modes WCM, notamment le mode PERMISSIF
 * pour la validation des longueurs de rouleaux
 */
window.wcmValidationService = {
    // Cache des modes WCM
    _modesCache: null,
    _cacheTimestamp: null,
    _cacheExpiry: 30000, // 30 secondes
    
    // État de loading
    _isLoading: false,
    
    /**
     * Initialise le service
     */
    init() {
        console.log('WCM Validation Service initialisé');
        
        // Écouter les changements de modes depuis le composant WCM
        if (window.eventBus) {
            window.eventBus.on('wcm:mode-toggled', (data) => {
                this.invalidateCache();
                this.updateStore();
                console.log('Cache WCM invalidé et store mis à jour suite à changement mode:', data);
            });
        }
        
        // Précharger les modes au démarrage
        this.loadModes().then(() => {
            this.updateStore();
        });
    },
    
    /**
     * Charge les modes WCM depuis l'API ou le cache
     */
    async loadModes() {
        // Vérifier le cache
        if (this._modesCache && this._cacheTimestamp) {
            const now = Date.now();
            if (now - this._cacheTimestamp < this._cacheExpiry) {
                return this._modesCache;
            }
        }
        
        // Éviter les appels multiples simultanés
        if (this._isLoading) {
            return this._modesCache || [];
        }
        
        this._isLoading = true;
        
        try {
            const response = await fetch('/wcm/api/modes/');
            if (response.ok) {
                this._modesCache = await response.json();
                this._cacheTimestamp = Date.now();
                console.log('Modes WCM chargés dans le service:', this._modesCache);
            } else {
                console.error('Erreur chargement modes WCM dans le service:', response.status);
                this._modesCache = [];
            }
        } catch (error) {
            console.error('Erreur réseau modes WCM dans le service:', error);
            this._modesCache = [];
        } finally {
            this._isLoading = false;
        }
        
        return this._modesCache || [];
    },
    
    /**
     * Invalide le cache des modes
     */
    invalidateCache() {
        this._modesCache = null;
        this._cacheTimestamp = null;
        console.log('Cache modes WCM invalidé');
    },
    
    /**
     * Vérifie si le mode PERMISSIF est actif
     */
    async isPermissiveModeActive() {
        const modes = await this.loadModes();
        const permissivMode = modes.find(mode => 
            mode.name && mode.name.toUpperCase().includes('PERMISSIF')
        );
        
        const isActive = permissivMode ? permissivMode.is_enabled : false;
        console.log('Mode PERMISSIF actif:', isActive, permissivMode);
        
        return isActive;
    },
    
    /**
     * Valide si un rouleau peut être sauvé selon les règles WCM
     */
    async validateRollSave(rollData, targetLength) {
        try {
            // Si pas de longueur cible définie, pas de validation WCM
            if (!targetLength || targetLength <= 0) {
                return {
                    valid: true,
                    reason: null
                };
            }
            
            // Si pas de longueur de rouleau, pas de validation
            if (!rollData.length || rollData.length <= 0) {
                return {
                    valid: true,
                    reason: null
                };
            }
            
            // Si rouleau non conforme, pas de validation WCM (déjà géré par la découpe)
            if (rollData.conformity_status === 'NON_CONFORME') {
                return {
                    valid: true,
                    reason: null
                };
            }
            
            // Vérifier le mode PERMISSIF pour les rouleaux conformes
            const isPermissivActive = await this.isPermissiveModeActive();
            
            if (!isPermissivActive) {
                // En mode strict : longueur rouleau DOIT être égale à la cible
                const rollLength = parseFloat(rollData.length);
                const target = parseFloat(targetLength);
                
                // Tolérance minimale pour les flottants
                const tolerance = 0.01;
                const lengthDifference = Math.abs(rollLength - target);
                
                if (lengthDifference > tolerance) {
                    return {
                        valid: false,
                        reason: 'Mode STRICT actif : la longueur du rouleau doit être égale à la longueur cible'
                    };
                }
            }
            
            return {
                valid: true,
                reason: null
            };
            
        } catch (error) {
            console.error('Erreur validation WCM:', error);
            // En cas d'erreur, autoriser la sauvegarde (mode dégradé)
            return {
                valid: true,
                reason: null
            };
        }
    },
    
    /**
     * Obtient le nom du mode PERMISSIF depuis le cache
     */
    async getPermissiveModeName() {
        const modes = await this.loadModes();
        const permissivMode = modes.find(mode => 
            mode.name && mode.name.toUpperCase().includes('PERMISSIF')
        );
        return permissivMode ? permissivMode.name : 'PERMISSIF';
    },
    
    /**
     * Met à jour le store Alpine.js
     */
    async updateStore() {
        if (window.Alpine && Alpine.store('wcmValidation')) {
            const isActive = await this.isPermissiveModeActive();
            Alpine.store('wcmValidation').isPermissivActive = isActive;
            Alpine.store('wcmValidation').lastUpdate = Date.now();
            console.log('Store WCM mis à jour:', { isPermissivActive: isActive });
        }
    },
    
    /**
     * Force le rechargement des modes
     */
    async refresh() {
        this.invalidateCache();
        const result = await this.loadModes();
        await this.updateStore();
        return result;
    }
};

// Initialisation immédiate du store Alpine.js
if (typeof Alpine !== 'undefined') {
    if (!Alpine.store('wcmValidation')) {
        Alpine.store('wcmValidation', {
            isPermissivActive: false,
            lastUpdate: Date.now()
        });
    }
} else {
    // Attendre que Alpine soit disponible
    document.addEventListener('alpine:init', () => {
        if (!Alpine.store('wcmValidation')) {
            Alpine.store('wcmValidation', {
                isPermissivActive: false,
                lastUpdate: Date.now()
            });
        }
    });
}

// Initialisation automatique quand le DOM est prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.wcmValidationService.init();
    });
} else {
    window.wcmValidationService.init();
}