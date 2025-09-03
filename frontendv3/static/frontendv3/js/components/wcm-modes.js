/**
 * Gestionnaire des modes WCM pour l'onglet Params&Specs
 * Permet de visualiser et toggle les modes de fonctionnement
 */
function wcmModesManager() {
    return {
        wcmModes: [],
        loadingToggle: null,
        error: null,

        /**
         * Initialisation du composant
         */
        init() {
            console.log('WCM Modes Manager initialisé');
            this.loadModes();
        },

        /**
         * Charge les modes WCM depuis l'API
         */
        async loadModes() {
            try {
                const response = await fetch('/wcm/api/modes/');
                if (response.ok) {
                    this.wcmModes = await response.json();
                    console.log('Modes WCM chargés:', this.wcmModes);
                } else {
                    console.error('Erreur chargement modes WCM:', response.status);
                    this.error = 'Erreur lors du chargement des modes';
                }
            } catch (error) {
                console.error('Erreur réseau modes WCM:', error);
                this.error = 'Erreur de connexion';
                this.wcmModes = [];
            }
        },

        /**
         * Toggle un mode WCM (activer/désactiver)
         */
        async toggleMode(modeId) {
            this.loadingToggle = modeId;
            this.error = null;

            try {
                const response = await fetch(`/wcm/api/modes/${modeId}/toggle/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });

                if (response.ok) {
                    const updatedMode = await response.json();
                    
                    // Mettre à jour le mode dans la liste locale
                    const modeIndex = this.wcmModes.findIndex(m => m.id === modeId);
                    if (modeIndex !== -1) {
                        this.wcmModes[modeIndex].is_enabled = updatedMode.is_enabled;
                    }
                    
                    // Mettre à jour immédiatement le cache du service de validation
                    if (window.wcmValidationService) {
                        // Mettre à jour le mode dans le cache du service
                        if (window.wcmValidationService._modesCache) {
                            const serviceModeIndex = window.wcmValidationService._modesCache.findIndex(m => m.id === modeId);
                            if (serviceModeIndex !== -1) {
                                window.wcmValidationService._modesCache[serviceModeIndex].is_enabled = updatedMode.is_enabled;
                            }
                        }
                    }

                    // Afficher feedback utilisateur
                    this.showFeedback(
                        `Mode ${updatedMode.name} ${updatedMode.is_enabled ? 'activé' : 'désactivé'}`,
                        'success'
                    );
                    
                    // Notifier le service de validation WCM via l'event bus
                    if (window.eventBus) {
                        window.eventBus.emit('wcm:mode-toggled', {
                            modeId: modeId,
                            modeName: updatedMode.name,
                            isEnabled: updatedMode.is_enabled
                        });
                    }

                } else {
                    const error = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
                    this.showFeedback(`Erreur: ${error.error || error.message || 'Impossible de modifier le mode'}`, 'error');
                }
            } catch (error) {
                console.error('Erreur toggle mode:', error);
                this.showFeedback('Erreur de connexion', 'error');
            } finally {
                this.loadingToggle = null;
            }
        },

        /**
         * Obtient le token CSRF
         */
        getCsrfToken() {
            // Utiliser la fonction getCookie du template de base si disponible
            if (window.getCookie) {
                return window.getCookie('csrftoken');
            }
            
            // Fallback vers les balises meta ou cookies
            const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                         document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            return token || '';
        },

        /**
         * Affiche un feedback à l'utilisateur
         */
        showFeedback(message, type = 'info') {
            // Pour l'instant, utiliser console + alert simple
            // TODO: Remplacer par des toasts plus élégants
            console.log(`[${type.toUpperCase()}] ${message}`);
            
            if (type === 'error') {
                // Afficher les erreurs de manière visible
                this.error = message;
                // Auto-clear après 5 secondes
                setTimeout(() => {
                    if (this.error === message) {
                        this.error = null;
                    }
                }, 5000);
            } else if (type === 'success') {
                // Flash success temporaire
                const successEl = document.createElement('div');
                successEl.className = 'alert alert-success alert-dismissible fade show position-fixed';
                successEl.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
                successEl.innerHTML = `
                    <i class="bi bi-check-circle me-2"></i>${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(successEl);
                
                // Auto-remove après 3 secondes
                setTimeout(() => {
                    if (successEl.parentNode) {
                        successEl.remove();
                    }
                }, 3000);
            }
        },

        /**
         * Rafraîchit les modes (utile après changements externes)
         */
        async refresh() {
            await this.loadModes();
        }
    };
}