/**
 * Composant Alpine.js : Modale de création d'opérateur
 * Gère la création de nouveaux opérateurs
 */

function createOperatorModal() {
    return {
        // État du formulaire
        firstName: '',
        lastName: '',
        trainingCompleted: false,
        
        // État de l'interface
        isCreating: false,
        errorMessage: '',
        
        // Modal Bootstrap instance
        modalInstance: null,
        
        // Initialisation
        init() {
            debug('Create Operator Modal initialized');
            
            // Récupérer l'instance Bootstrap de la modale
            this.modalInstance = new bootstrap.Modal(this.$el);
            
            // Nettoyer le formulaire à la fermeture
            this.$el.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
            });
        },
        
        // Propriétés calculées
        get canCreate() {
            return this.firstName.trim().length > 0 && this.lastName.trim().length > 0;
        },
        
        // Réinitialiser le formulaire
        resetForm() {
            this.firstName = '';
            this.lastName = '';
            this.trainingCompleted = false;
            this.errorMessage = '';
            this.isCreating = false;
        },
        
        // Afficher la modale
        show() {
            this.resetForm();
            this.modalInstance.show();
            
            // Focus sur le premier champ après ouverture
            this.$el.addEventListener('shown.bs.modal', () => {
                const firstInput = this.$el.querySelector('#firstName');
                if (firstInput) {
                    firstInput.focus();
                }
            }, { once: true });
        },
        
        // Créer un nouvel opérateur
        async createOperator() {
            if (!this.canCreate || this.isCreating) {
                return;
            }
            
            this.isCreating = true;
            this.errorMessage = '';
            
            try {
                // Préparer les données avec formatage
                const firstName = this.firstName.trim();
                const formattedFirstName = firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
                
                const operatorData = {
                    first_name: formattedFirstName,
                    last_name: this.lastName.trim().toUpperCase(),
                    training_completed: this.trainingCompleted,
                    is_active: true // Toujours actif par défaut
                };
                
                debug('Creating operator with data:', operatorData);
                
                // Appeler l'API
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                const response = await fetch('/planification/api/operators/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(operatorData)
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
                }
                
                const createdOperator = await response.json();
                debug('Operator created successfully:', createdOperator);
                
                // Fermer la modale
                this.modalInstance.hide();
                
                // Notifier le succès
                showNotification('success', `Opérateur ${createdOperator.first_name} ${createdOperator.last_name} créé avec succès !`);
                
                // Recharger la liste des opérateurs et sélectionner le nouveau
                await this.refreshOperatorList(createdOperator.employee_id);
                
            } catch (error) {
                debug('Error creating operator:', error);
                this.errorMessage = error.message || 'Erreur lors de la création de l\'opérateur';
            } finally {
                this.isCreating = false;
            }
        },
        
        // Recharger la liste des opérateurs
        async refreshOperatorList(newOperatorId) {
            try {
                // Recharger les données opérateurs depuis l'API
                const response = await fetch('/planification/api/operators/');
                if (response.ok) {
                    const operators = await response.json();
                    
                    // Convertir au format attendu par les composants
                    const operatorsData = operators.map(op => ({
                        id: op.id,
                        employee_id: op.employee_id,
                        first_name: op.first_name,
                        last_name: op.last_name,
                        display_name: `${op.first_name} ${op.last_name}`,
                        training_completed: op.training_completed
                    }));
                    
                    // Mettre à jour les données globales
                    window.operatorsData = operatorsData;
                    
                    // Notifier les composants de se mettre à jour
                    window.dispatchEvent(new CustomEvent('operators-updated', {
                        detail: { 
                            operators: operatorsData
                        }
                    }));
                }
            } catch (error) {
                debug('Error refreshing operator list:', error);
                // On continue même si la mise à jour échoue
            }
        }
    };
}

// Export global pour Alpine
window.createOperatorModal = createOperatorModal;