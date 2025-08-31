/**
 * Composant Alpine.js : Ordre de Fabrication
 * Gère la sélection des OF et découpe
 */

function productionOrder() {
    // Charger les données sauvegardées AVANT l'initialisation
    const savedData = window.sessionData?.of || {};
    
    return {
        // Mixin
        ...window.sessionMixin,
        // État local avec les valeurs sauvegardées
        ofEnCours: savedData.ofEnCours || '',
        ofDecoupe: savedData.ofDecoupe || '',
        targetLength: savedData.targetLength || 0,
        fabricationOrders: window.fabricationOrdersData || [],
        cuttingOrders: window.cuttingOrdersData || [],
        
        // États de verrouillage (verrouillés par défaut)
        ofEnCoursLocked: savedData.ofEnCoursLocked !== undefined ? savedData.ofEnCoursLocked : true,
        targetLengthLocked: savedData.targetLengthLocked !== undefined ? savedData.targetLengthLocked : true,
        ofDecoupeLocked: savedData.ofDecoupeLocked !== undefined ? savedData.ofDecoupeLocked : true,
        
        
        // Initialisation
        init() {
            debug('Production order initialized');
            
            // Initialiser le mixin session
            this.initSession();
            
            // Observer les changements
            this.$watch('ofEnCours', () => this.handleOFChange());
            this.$watch('ofDecoupe', () => this.saveProductionData());
            this.$watch('targetLength', () => this.saveProductionData());
            
            // Observer les changements d'état de verrouillage
            this.$watch('ofEnCoursLocked', () => this.saveLockStates());
            this.$watch('targetLengthLocked', () => this.saveLockStates());
            this.$watch('ofDecoupeLocked', () => this.saveLockStates());
            
            // Écouter la mise à jour de la liste des OF
            window.addEventListener('fabrication-orders-updated', (event) => {
                const data = event.detail;
                if (data.fabricationOrders) {
                    // Mettre à jour les listes locales SEULEMENT
                    this.fabricationOrders = data.fabricationOrders;
                    this.cuttingOrders = data.cuttingOrders;
                    // NE PAS sélectionner automatiquement
                }
            });
            
            // Appliquer les styles initiaux après le rendu
            this.$nextTick(() => {
                this.updateFieldStyles();
                
                // FORCE les valeurs dans les inputs après le rendu
                if (this.ofEnCours) {
                    const select = this.$el.querySelector('select[x-model="ofEnCours"]');
                    if (select) select.value = this.ofEnCours;
                }
                if (this.ofDecoupe) {
                    const select = this.$el.querySelector('select[x-model="ofDecoupe"]');
                    if (select) select.value = this.ofDecoupe;
                }
                if (this.targetLength) {
                    const input = this.$el.querySelector('input[x-model="targetLength"]');
                    if (input) input.value = this.targetLength;
                }
            });
        },
        
        // Mettre à jour les styles des champs
        updateFieldStyles() {
            const ofEnCoursSelect = this.$el.querySelector('select[x-model="ofEnCours"]');
            const ofDecoupeSelect = this.$el.querySelector('select[x-model="ofDecoupe"]');
            const targetLengthInput = this.$el.querySelector('input[x-model="targetLength"]');
            
            if (ofEnCoursSelect) ofEnCoursSelect.classList.toggle('filled', !!this.ofEnCours);
            if (ofDecoupeSelect) ofDecoupeSelect.classList.toggle('filled', !!this.ofDecoupe);
            if (targetLengthInput) targetLengthInput.classList.toggle('filled', this.targetLength > 0);
        },
        
        // Gestion du changement d'OF
        handleOFChange() {
            // NE PAS écraser la longueur cible si elle existe déjà en session
            // Seulement la mettre à jour si c'est un nouveau OF ou si elle est à 0
            const selectedOF = this.fabricationOrders.find(of => of.numero === this.ofEnCours);
            if (selectedOF && this.targetLength === 0) {
                // Seulement si pas de longueur cible définie
                this.targetLength = selectedOF.target_length || 0;
            } else if (!selectedOF) {
                this.targetLength = 0;
            }
            
            // Émettre l'événement pour la grille
            window.eventBus.emit(window.eventBus.EVENTS.TARGET_LENGTH_CHANGED, {
                length: this.targetLength
            });
            
            this.saveProductionData();
        },
        
        // Sauvegarder dans la session
        saveProductionData() {
            const data = {
                ofEnCours: this.ofEnCours,
                ofDecoupe: this.ofDecoupe,
                targetLength: this.targetLength,
                ofEnCoursLocked: this.ofEnCoursLocked,
                targetLengthLocked: this.targetLengthLocked,
                ofDecoupeLocked: this.ofDecoupeLocked
            };
            
            // Utiliser la sauvegarde du mixin
            this.saveToSession({ of: data });
            
            // Émettre l'événement pour la sticky bar
            window.dispatchEvent(new CustomEvent('of-changed', {
                detail: { ofNumber: this.ofEnCours }
            }));
        },
        
        // Sauvegarder les états de verrouillage
        saveLockStates() {
            const data = {
                ofEnCours: this.ofEnCours,
                ofDecoupe: this.ofDecoupe,
                targetLength: this.targetLength,
                ofEnCoursLocked: this.ofEnCoursLocked,
                targetLengthLocked: this.targetLengthLocked,
                ofDecoupeLocked: this.ofDecoupeLocked
            };
            
            this.saveToSession({ of: data });
        },
        
        // Handlers pour les changements
        handleOFEnCoursChange(event) {
            this.ofEnCours = event.target.value;
            event.target.classList.toggle('filled', !!this.ofEnCours);
        },
        
        handleOFDecoupeChange(event) {
            this.ofDecoupe = event.target.value;
            event.target.classList.toggle('filled', !!this.ofDecoupe);
        },
        
        handleTargetLengthChange(event) {
            let value = parseFloat(event.target.value) || 0;
            
            // Limiter à des valeurs raisonnables (max 1000m)
            if (value > 1000) {
                value = 1000;
                event.target.value = value;
            }
            
            this.targetLength = value;
            event.target.classList.toggle('filled', value > 0);
            
            // Sauvegarder quand on change manuellement
            this.saveProductionData();
            
            // Émettre l'événement pour la grille (ancien système qui fonctionnait)
            window.dispatchEvent(new CustomEvent('target-length-changed', {
                detail: { length: this.targetLength }
            }));
        },
        
        // Nouveau handler pour le blur avec re-verrouillage
        handleTargetLengthBlur(event) {
            // D'abord traiter le changement
            this.handleTargetLengthChange(event);
            // Puis re-verrouiller
            this.lockTargetLength();
        },
        
        // Méthodes de basculement du verrouillage
        toggleOFEnCoursLock() {
            this.ofEnCoursLocked = !this.ofEnCoursLocked;
            debug('OF en cours lock toggled:', this.ofEnCoursLocked);
        },
        
        toggleTargetLengthLock() {
            this.targetLengthLocked = !this.targetLengthLocked;
            debug('Target length lock toggled:', this.targetLengthLocked);
        },
        
        toggleOFDecoupeLock() {
            this.ofDecoupeLocked = !this.ofDecoupeLocked;
            debug('OF découpe lock toggled:', this.ofDecoupeLocked);
        },
        
        // Méthodes de verrouillage automatique (pour le blur)
        lockOFEnCours() {
            this.ofEnCoursLocked = true;
            debug('OF en cours auto-locked');
        },
        
        lockTargetLength() {
            this.targetLengthLocked = true;
            debug('Target length auto-locked');
        },
        
        lockOFDecoupe() {
            this.ofDecoupeLocked = true;
            debug('OF découpe auto-locked');
        },
        
        // Afficher la modale de création d'OF
        showCreateOFModal() {
            const modalElement = document.querySelector('#createOFModal');
            if (modalElement && modalElement._x_dataStack) {
                const modalComponent = modalElement._x_dataStack[0];
                modalComponent.show();
            }
        }
    };
}

// Export global pour Alpine
window.productionOrder = productionOrder;