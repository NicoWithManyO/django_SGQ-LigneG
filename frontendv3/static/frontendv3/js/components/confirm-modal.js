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
        selectedMood: null, // Pas de sélection par défaut
        saveSuccess: false, // État de succès après sauvegarde
        
        // Initialisation
        init() {
            debug('Confirm modal initialized');
            
            // Créer l'instance Bootstrap
            this.modalInstance = new bootstrap.Modal('#confirmModal', {
                backdrop: 'static', // Empêche la fermeture en cliquant à l'extérieur
                keyboard: true      // Permet la fermeture avec Escape
            });
            
            // Écouter l'événement de fermeture pour réinitialiser l'état
            document.getElementById('confirmModal').addEventListener('hidden.bs.modal', async () => {
                // Incrémenter le compteur de mood si on a sélectionné un mood
                if (this.selectedMood && this.saveSuccess) {
                    try {
                        const response = await fetch('/wcm/api/mood-counter/increment/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                            },
                            body: JSON.stringify({ mood: this.selectedMood })
                        });
                        
                        if (response.ok) {
                            debug('Compteur mood incrémenté:', this.selectedMood);
                        }
                    } catch (error) {
                        console.error('Erreur incrémentation mood:', error);
                    }
                }
                
                this.resetModal();
            });
        },
        
        // Afficher la modale avec une configuration
        show(config) {
            // Fusionner la config
            Object.assign(this.modalConfig, config);
            
            // Réinitialiser l'état
            this.modalProcessing = false;
            this.saveSuccess = false;
            this.selectedMood = null; // Pas de mood sélectionné par défaut
            
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
                
                // Marquer comme succès
                this.saveSuccess = true;
                
                // Changer le texte du bouton
                this.modalConfig.confirmText = 'Sauvegardé avec succès !';
                this.modalConfig.confirmIcon = 'bi-check-circle-fill';
                this.modalConfig.confirmClass = 'btn-success';
                
                // Ne pas fermer automatiquement - l'utilisateur doit fermer manuellement
                
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
                confirmAction: null,
                showComment: false,
                commentValue: '',
                question: ''
            };
            this.modalProcessing = false;
            
            debug('Modal reset');
        }
    };
};