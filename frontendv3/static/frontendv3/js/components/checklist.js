/**
 * Composant Alpine.js : Check-list prise de poste
 * Gestion de la check-list avec options OK/N/A/NOK
 */

function checklist() {
    const savedData = window.sessionData?.checklist || {};
    
    return {
        // Mixins
        ...collapsibleMixin(true),
        ...window.sessionMixin,
        
        // État local
        responses: savedData.responses || {},
        comments: savedData.comments || {},
        signature: savedData.signature || '',
        signatureTime: savedData.signatureTime || '',
        signatureError: false,
        items: [],
        lastOperatorId: null,
        
        // Initialisation
        init() {
            debug('Checklist initialized');
            
            // Initialiser les mixins
            this.initCollapsible();
            this.initSession();
            
            // Charger les items de check-list
            this.loadChecklistItems();
            
            // Émettre l'état initial
            this.$nextTick(() => {
                window.dispatchEvent(new CustomEvent('checklist-signed-changed', { 
                    detail: { signed: !!this.signature && this.isComplete }
                }));
            });
            
            // Observer les changements pour sauvegarder
            this.$watch('responses', () => {
                // Si la check-list n'est plus complète, vider la signature
                if (!this.isComplete && this.signature) {
                    this.signature = '';
                    this.signatureTime = '';
                    this.signatureError = false;
                    // Émettre l'événement
                    window.dispatchEvent(new CustomEvent('checklist-signed-changed', { 
                        detail: { signed: false }
                    }));
                }
                this.saveChecklistData();
            }, { deep: true });
            
            // Observer les changements de commentaires
            this.$watch('comments', () => {
                this.saveChecklistData();
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
                    // Émettre l'événement
                    window.dispatchEvent(new CustomEvent('checklist-signed-changed', { 
                        detail: { signed: false }
                    }));
                    this.saveChecklistData();
                    if (this.signature || this.signatureTime) {
                        showNotification('info', 'Signature réinitialisée (changement d\'opérateur)');
                    }
                }
            });
            
            // Écouter la réinitialisation après sauvegarde du shift
            window.addEventListener('shift-reset', () => {
                debug('Réinitialisation de la checklist après sauvegarde du shift');
                // Réinitialiser toutes les réponses et commentaires
                this.items.forEach(item => {
                    this.responses[item.id] = '';
                    delete this.comments[item.id];
                });
                this.comments = {};
                this.signature = '';
                this.signatureTime = '';
                this.signatureError = false;
                this.lastOperatorId = null;
                
                // Émettre l'événement
                window.dispatchEvent(new CustomEvent('checklist-signed-changed', { 
                    detail: { signed: false }
                }));
                
                this.saveChecklistData();
                showNotification('info', 'Checklist réinitialisée pour le prochain poste');
            });
            
            // Mémoriser l'opérateur actuel
            this.lastOperatorId = window.sessionData?.shift?.operatorId;
        },
        
        // Charger les items depuis l'API
        async loadChecklistItems() {
            try {
                const response = await fetch('/wcm/api/checklist-template-default/');
                if (!response.ok) throw new Error('Erreur chargement template');
                
                const data = await response.json();
                
                // Mapper les items pour le format attendu
                this.items = data.items.map(item => ({
                    id: item.id,
                    text: item.text
                }));
                
                debug('Checklist items loaded:', this.items);
                
                // Sauvegarder les items en session pour le backend
                this.saveChecklistData();
                
            } catch (error) {
                console.error('Erreur chargement checklist:', error);
                // Fallback sur des items par défaut si erreur
                this.items = [
                    { id: 1, text: "Erreur de chargement - Item 1" }
                ];
            }
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
            
            // Si on passe de NOK à autre chose, nettoyer le commentaire
            if (option !== 'NOK' && this.comments[itemId]) {
                delete this.comments[itemId];
                this.comments = { ...this.comments };
            }
            
            // Forcer la mise à jour de l'UI
            this.responses = { ...this.responses };
            
            // Si on a cliqué sur NOK, focus le champ de commentaire
            if (option === 'NOK') {
                // Émettre un événement pour focus ce champ spécifique
                window.dispatchEvent(new CustomEvent('focus-nok-comment', { 
                    detail: { itemId: itemId }
                }));
            }
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
        saveChecklistData() {
            // Créer un objet items avec id -> text ET garder l'ordre
            const itemsMap = {};
            const itemsOrder = [];
            this.items.forEach(item => {
                itemsMap[item.id] = item.text;
                itemsOrder.push(item.id);
            });
            
            const data = {
                items: itemsMap,
                itemsOrder: itemsOrder,  // Garder l'ordre des items
                responses: this.responses,
                comments: this.comments,
                signature: this.signature,
                signatureTime: this.signatureTime
            };
            this.saveToSession({ checklist: data });
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
            
            // Extraire les initiales de l'employee_id
            // Format attendu: PrenomNOM (ex: "StéphaneMALLET" -> "SM")
            let expectedInitials = '';
            
            // Trouver la transition prénom -> nom (minuscule vers majuscule)
            let match = operatorId.match(/^([A-Za-z])[a-z]*([A-Z])/);
            if (match) {
                // Première lettre du prénom + première lettre du nom
                expectedInitials = match[1].toUpperCase() + match[2];
            } else {
                // Fallback: chercher les lettres majuscules
                const majuscules = operatorId.match(/[A-Z]/g);
                if (majuscules && majuscules.length >= 2) {
                    // Prendre première et deuxième majuscule
                    expectedInitials = majuscules[0] + majuscules[1];
                } else if (operatorId.length >= 2) {
                    // Dernier recours: deux premières lettres
                    expectedInitials = operatorId.substring(0, 2).toUpperCase();
                } else {
                    showNotification('error', 'Format opérateur invalide pour la signature');
                    this.signature = '';
                    return;
                }
            }
            
            // Vérifier que la signature correspond aux initiales
            if (this.signature.toUpperCase() !== expectedInitials) {
                showNotification('error', `Les initiales doivent être "${expectedInitials}"`);
                this.signatureTime = ''; // Reset l'heure
                this.signatureError = true; // Marquer l'erreur
                this.saveChecklistData();
                return;
            }
            
            // Sauvegarder avec l'heure
            this.signatureError = false; // Pas d'erreur
            this.signatureTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
            this.saveChecklistData();
            showNotification('success', 'Check-list signée');
            
            // Émettre l'événement de signature
            window.dispatchEvent(new CustomEvent('checklist-signed-changed', { 
                detail: { signed: true }
            }));
        }
    };
}

// Export global pour Alpine
window.checklist = checklist;