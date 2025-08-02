/**
 * Mixin réutilisable pour gérer les tooltips Bootstrap
 * Fournit une gestion centralisée et DRY des tooltips
 */

window.tooltipMixin = {
    _tooltip: null,
    
    /**
     * Initialise un tooltip sur un élément
     * @param {HTMLElement} element - L'élément sur lequel attacher le tooltip
     * @param {Function|String} getMessage - Fonction ou string retournant le message
     */
    initTooltip(element, getMessage) {
        console.log('initTooltip appelé, Bootstrap disponible:', !!window.bootstrap?.Tooltip);
        
        if (!element || !window.bootstrap?.Tooltip) {
            console.error('Tooltip: Bootstrap non disponible ou élément manquant');
            debug('Tooltip: Bootstrap non disponible ou élément manquant');
            return;
        }
        
        // Obtenir le message
        const message = typeof getMessage === 'function' ? getMessage() : getMessage;
        
        // Si pas de message, pas de tooltip
        if (!message) {
            return;
        }
        
        // Détruire l'ancien tooltip s'il existe
        if (this._tooltip) {
            this.destroyTooltip();
        }
        
        // Configurer l'élément pour Bootstrap
        element.setAttribute('data-bs-toggle', 'tooltip');
        element.setAttribute('data-bs-placement', 'top');
        element.setAttribute('data-bs-title', message);
        
        // Créer et afficher le tooltip immédiatement
        try {
            this._tooltip = new bootstrap.Tooltip(element, {
                trigger: 'manual', // On gère manuellement l'affichage
                container: 'body',
                html: true
            });
            this._tooltip.show();
            
            console.log('Tooltip créé et affiché:', message);
            debug('Tooltip créé:', message);
        } catch (e) {
            console.error('Erreur création tooltip:', e);
        }
    },
    
    /**
     * Détruit le tooltip actuel
     */
    destroyTooltip() {
        if (this._tooltip) {
            try {
                this._tooltip.hide();
                this._tooltip.dispose();
                debug('Tooltip détruit');
            } catch (e) {
                // Ignorer les erreurs si le tooltip est déjà détruit
            }
            this._tooltip = null;
        }
    },
    
    /**
     * Setup du tooltip avec gestion hover automatique
     * @param {HTMLElement} element - L'élément sur lequel attacher le tooltip
     * @param {Function|String} getMessage - Fonction ou string retournant le message
     */
    setupTooltip(element, getMessage) {
        if (!element || !window.bootstrap?.Tooltip) {
            return;
        }
        
        // Nettoyer tout tooltip existant sur cet élément
        const existingTooltip = bootstrap.Tooltip.getInstance(element);
        if (existingTooltip) {
            existingTooltip.dispose();
        }
        
        // Fonction pour mettre à jour le titre
        const updateTitle = () => {
            const message = typeof getMessage === 'function' ? getMessage() : getMessage;
            if (message) {
                element.setAttribute('data-bs-title', message);
                element.setAttribute('title', message); // Fallback
            } else {
                element.removeAttribute('data-bs-title');
                element.removeAttribute('title');
            }
        };
        
        // Mettre à jour le titre initial
        updateTitle();
        
        // Si on a un message, créer le tooltip
        const message = typeof getMessage === 'function' ? getMessage() : getMessage;
        if (message) {
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
            new bootstrap.Tooltip(element);
        }
        
        // Retourner la fonction de mise à jour pour usage externe
        return updateTitle;
    }
};

// Export pour utilisation dans les composants
debug('✅ Tooltip mixin chargé');