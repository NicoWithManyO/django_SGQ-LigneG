/**
 * Composant Alpine.js : Modale de création d'OF
 * Gère la création de nouveaux ordres de fabrication
 */

function createOFModal() {
    return {
        // État du formulaire
        ofNumber: '',
        requiredLength: '',
        targetRollLength: '',
        
        // État de l'interface
        isCreating: false,
        errorMessage: '',
        
        // Modal Bootstrap instance
        modalInstance: null,
        
        // Initialisation
        init() {
            debug('Create OF Modal initialized');
            
            // Récupérer l'instance Bootstrap de la modale
            this.modalInstance = new bootstrap.Modal(this.$el);
            
            // Nettoyer le formulaire à la fermeture
            this.$el.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
            });
        },
        
        // Propriétés calculées
        get canCreate() {
            return this.ofNumber.trim().length > 0;
        },
        
        // Réinitialiser le formulaire
        resetForm() {
            this.ofNumber = '';
            this.requiredLength = '';
            this.targetRollLength = '';
            this.errorMessage = '';
            this.isCreating = false;
        },
        
        // Afficher la modale
        show() {
            this.resetForm();
            this.modalInstance.show();
            
            // Focus sur le premier champ après ouverture
            this.$el.addEventListener('shown.bs.modal', () => {
                const firstInput = this.$el.querySelector('#ofNumber');
                if (firstInput) {
                    firstInput.focus();
                }
            }, { once: true });
        },
        
        // Créer un nouvel OF
        async createOF() {
            if (!this.canCreate || this.isCreating) {
                return;
            }
            
            this.isCreating = true;
            this.errorMessage = '';
            
            try {
                // Préparer les données
                const ofData = {
                    order_number: this.ofNumber.trim(),
                    required_length: this.requiredLength ? parseFloat(this.requiredLength) : null,
                    target_roll_length: this.targetRollLength ? parseFloat(this.targetRollLength) : null
                };
                
                debug('Creating OF with data:', ofData);
                
                // Appeler l'API
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                const response = await fetch('/planification/api/fabrication-orders/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(ofData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
                }
                
                const createdOF = await response.json();
                debug('OF created successfully:', createdOF);
                
                // Fermer la modale
                this.modalInstance.hide();
                
                // Notifier le succès
                showNotification('success', `OF ${createdOF.order_number} créé avec succès !`);
                
                // Recharger la liste des OF et sélectionner le nouveau
                await this.refreshOFList(createdOF.order_number);
                
            } catch (error) {
                debug('Error creating OF:', error);
                this.errorMessage = error.message || 'Erreur lors de la création de l\'OF';
            } finally {
                this.isCreating = false;
            }
        },
        
        // Recharger la liste des OF et sélectionner le nouveau
        async refreshOFList(newOFNumber) {
            try {
                // Recharger les données OF depuis l'API
                const response = await fetch('/planification/api/fabrication-orders/');
                if (response.ok) {
                    const apiData = await response.json();
                    
                    // Convertir au format attendu par les composants
                    const fabricationOrders = apiData.fabrication_orders.map(of => ({
                        id: of.id,
                        numero: of.order_number,
                        target_length: of.target_roll_length || 0
                    }));
                    
                    const cuttingOrders = apiData.cutting_orders.map(of => ({
                        id: of.id,
                        numero: of.order_number,
                        target_length: 0
                    }));
                    
                    // Mettre à jour les données globales
                    window.fabricationOrdersData = fabricationOrders;
                    window.cuttingOrdersData = cuttingOrders;
                    
                    // Notifier les composants de se mettre à jour
                    window.dispatchEvent(new CustomEvent('fabrication-orders-updated', {
                        detail: { 
                            fabricationOrders: fabricationOrders,
                            cuttingOrders: cuttingOrders
                        }
                    }));
                }
            } catch (error) {
                debug('Error refreshing OF list:', error);
                // On continue même si la mise à jour échoue
            }
        }
    };
}

// Export global pour Alpine
window.createOFModal = createOFModal;