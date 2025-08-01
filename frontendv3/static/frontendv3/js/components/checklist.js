/**
 * Composant Alpine.js : Check-list prise de poste
 * Gestion de la check-list avec options OK/N/A/NOK
 */

function checklist() {
    const savedData = window.sessionData?.checklist || {};
    
    return {
        // Mixin pour la fonctionnalité collapsible
        ...collapsibleMixin(true),
        
        // État local
        responses: savedData.responses || {},
        signature: savedData.signature || '',
        signatureTime: savedData.signatureTime || '',
        signatureError: false,
        items: [],
        lastOperatorId: null,
        
        // Initialisation
        init() {
            debug('Checklist initialized');
            
            // Initialiser le comportement collapsible
            this.initCollapsible();
            
            // Charger les items de check-list
            this.loadChecklistItems();
            
            // Observer les changements pour sauvegarder
            this.$watch('responses', () => {
                // Si la check-list n'est plus complète, vider la signature
                if (!this.isComplete && this.signature) {
                    this.signature = '';
                    this.signatureTime = '';
                    this.signatureError = false;
                }
                this.saveToSession();
            }, { deep: true });
            
            // Observer les changements d'opérateur
            window.addEventListener('operator-changed', (event) => {
                const newOperatorId = event.detail.operatorId;
                if (newOperatorId !== this.lastOperatorId) {
                    this.lastOperatorId = newOperatorId;
                    // Toujours vider la signature si l'opérateur change
                    this.signature = '';
                    this.signatureTime = '';
                    this.signatureError = false;
                    this.saveToSession();
                    if (this.signature || this.signatureTime) {
                        showNotification('info', 'Signature réinitialisée (changement d\'opérateur)');
                    }
                }
            });
            
            // Mémoriser l'opérateur actuel
            this.lastOperatorId = window.sessionData?.shift?.operatorId;
        },
        
        // Charger les items depuis l'API ou données statiques
        async loadChecklistItems() {
            // Pour l'instant, utiliser des données statiques
            this.items = [
                { id: 1, text: "Les aspirations sont en cours et fonctionnent" },
                { id: 2, text: "Les paramètres machine correspondent au profil" },
                { id: 3, text: "Les soudures sont faites et correctes" },
                { id: 4, text: "Baguettes retirées - cohérent" },
                { id: 5, text: "Propreté du tambour" },
                { id: 6, text: "État du tapis Ensimeuse" },
                { id: 7, text: "4 buses du lavage tapis fonctionne" },
                { id: 8, text: "Le feutre sort sec de l'ensimeuse et pas brulé" },
                { id: 9, text: "Les découpes de l'enrouleur sont affutées" }
            ];
        },
        
        // Gérer le clic sur une option
        handleOptionClick(itemId, option) {
            // Si l'option est déjà sélectionnée, la désélectionner
            if (this.responses[itemId] === option) {
                delete this.responses[itemId];
            } else {
                // Sinon, sélectionner cette option
                this.responses[itemId] = option;
            }
            
            // Forcer la mise à jour de l'UI
            this.responses = { ...this.responses };
        },
        
        // Vérifier si une option est sélectionnée
        isSelected(itemId, option) {
            return this.responses[itemId] === option;
        },
        
        // Obtenir la classe CSS pour un bouton
        getButtonClass(itemId, option) {
            const isActive = this.isSelected(itemId, option);
            
            // Classes de base
            let classes = 'btn btn-sm ';
            
            // Classes selon l'option et l'état
            if (option === 'OK') {
                classes += isActive ? 'btn-success' : 'btn-outline-success';
            } else if (option === 'N/A') {
                classes += isActive ? 'btn-secondary' : 'btn-outline-secondary';
            } else if (option === 'NOK') {
                classes += isActive ? 'btn-danger' : 'btn-outline-danger';
            }
            
            return classes;
        },
        
        // Vérifier si la check-list est complète
        get isComplete() {
            return this.items.every(item => this.responses[item.id]);
        },
        
        // Compter les réponses
        get responseCount() {
            return Object.keys(this.responses).length;
        },
        
        // Sauvegarder dans la session
        saveToSession() {
            const data = {
                responses: this.responses,
                signature: this.signature,
                signatureTime: this.signatureTime
            };
            window.saveToSession('checklist', data);
        },
        
        // Sauvegarder la signature
        saveSignature() {
            if (!this.isComplete || !this.signature) return;
            
            // Récupérer l'opérateur sélectionné
            const operatorId = window.sessionData?.shift?.operatorId;
            if (!operatorId) {
                showNotification('error', 'Aucun opérateur sélectionné');
                this.signature = '';
                return;
            }
            
            // Extraire les initiales de l'employee_id (ex: "MartinDUPONT" -> "MD")
            const match = operatorId.match(/^([A-Z])[a-z]*([A-Z])/);
            if (!match) {
                showNotification('error', 'Format opérateur invalide');
                this.signature = '';
                return;
            }
            
            const expectedInitials = match[1] + match[2]; // Ex: "MD"
            
            // Vérifier que la signature correspond aux initiales
            if (this.signature.toUpperCase() !== expectedInitials) {
                showNotification('error', `Les initiales doivent être "${expectedInitials}"`);
                this.signatureTime = ''; // Reset l'heure
                this.signatureError = true; // Marquer l'erreur
                this.saveToSession();
                return;
            }
            
            // Sauvegarder avec l'heure
            this.signatureError = false; // Pas d'erreur
            this.signatureTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
            this.saveToSession();
            showNotification('success', 'Check-list signée');
        }
    };
}

// Export global pour Alpine
window.checklist = checklist;