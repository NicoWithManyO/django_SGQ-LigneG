/**
 * Composant Alpine.js : Modale de confirmation réutilisable
 * Gère les confirmations pour différentes actions (save shift, save roll, etc.)
 */
window.confirmModal = function() {
    return {
        // Configuration de la modale
        modalConfig: {
            title: '',
            icon: 'bi-save',
            content: '',
            warning: '',
            confirmText: 'Confirmer',
            confirmIcon: 'bi-check-circle',
            confirmClass: 'btn-primary',
            confirmAction: null
        },
        
        // État
        modalProcessing: false,
        modalInstance: null,
        selectedMood: 'happy', // Humeur par défaut
        
        // Initialisation
        init() {
            debug('Confirm modal initialized');
            
            // Créer l'instance Bootstrap
            this.modalInstance = new bootstrap.Modal('#confirmModal', {
                backdrop: 'static', // Empêche la fermeture en cliquant à l'extérieur
                keyboard: true      // Permet la fermeture avec Escape
            });
            
            // Écouter l'événement de fermeture pour réinitialiser l'état
            document.getElementById('confirmModal').addEventListener('hidden.bs.modal', () => {
                this.resetModal();
            });
        },
        
        // Afficher la modale avec une configuration
        show(config) {
            // Fusionner la config
            Object.assign(this.modalConfig, config);
            
            // Réinitialiser l'état de processing
            this.modalProcessing = false;
            
            // Afficher
            this.modalInstance.show();
            
            debug('Modal shown with config:', config);
        },
        
        // Exécuter l'action de confirmation
        async executeConfirm() {
            if (!this.modalConfig.confirmAction) {
                console.warn('Aucune action de confirmation définie');
                return;
            }
            
            this.modalProcessing = true;
            
            try {
                // Exécuter l'action
                await this.modalConfig.confirmAction();
                
                // Ne pas fermer automatiquement - l'utilisateur doit fermer manuellement
                // Cela permet de voir le résultat de l'action
                
            } catch (error) {
                console.error('Erreur lors de l\'exécution de l\'action:', error);
                showNotification('error', 'Une erreur est survenue lors de la sauvegarde');
                
            } finally {
                this.modalProcessing = false;
            }
        },
        
        // Fermer la modale
        close() {
            this.modalInstance.hide();
        },
        
        // Réinitialiser la modale
        resetModal() {
            this.modalConfig = {
                title: '',
                icon: 'bi-save',
                content: '',
                warning: '',
                confirmText: 'Confirmer',
                confirmIcon: 'bi-check-circle',
                confirmClass: 'btn-primary',
                confirmAction: null
            };
            this.modalProcessing = false;
            
            debug('Modal reset');
        }
    };
};