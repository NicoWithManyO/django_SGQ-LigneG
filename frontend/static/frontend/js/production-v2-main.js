/**
 * Script principal pour Production V2
 * Initialisation et coordination des composants
 */

// ===== INITIALISATION =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('Production V2 ready');
    
    // Injecter les données depuis Django si disponibles
    // (Ces données sont injectées par le template Django)
    
    // Charger les données
    if (window.loadOperators) loadOperators();
    if (window.loadFabricationOrders) loadFabricationOrders();
    
    // Le système de verrouillage est maintenant géré par field-lock-v2.js
    // qui s'initialise automatiquement
    
    // S'abonner aux changements de l'ID du shift après que le système soit prêt
    if (window.eventBus) {
        window.eventBus.on('system:ready', () => {
            // S'abonner aux changements d'ID
            if (window.stateManager) {
                window.stateManager.subscribe('shift.id', (newValue, oldValue, source) => {
                    const shiftIdDisplay = document.getElementById('shift-id-display');
                    if (shiftIdDisplay) {
                        
                        // Toujours mettre à jour si on a une nouvelle valeur non-null
                        if (newValue !== null && newValue !== undefined) {
                            shiftIdDisplay.textContent = newValue;
                            // Mettre à jour l'icône pour montrer que l'ID est valide
                            if (window.updateShiftIdStatusIcon) {
                                window.updateShiftIdStatusIcon('valid');
                            }
                        }
                        // Si newValue est null mais qu'on avait une ancienne valeur, la garder
                        else if (oldValue && !newValue) {
                            console.log('⚠️ Garde l\'ancien ID car le nouveau est null');
                        }
                    }
                });
                
                // S'abonner aux changements des champs du formulaire pour mettre à jour l'icône
                const checkShiftFormStatus = () => {
                    const shiftId = window.stateManager.getState('shift.id');
                    const operatorId = window.stateManager.getState('shift.operatorId');
                    const shiftDate = window.stateManager.getState('shift.date');
                    const vacation = window.stateManager.getState('shift.vacation');
                    
                    if (window.updateShiftIdStatusIcon) {
                        // Si pas d'ID, icône grise
                        if (!shiftId) {
                            window.updateShiftIdStatusIcon('empty');
                        } 
                        // Si ID présent et tous les champs remplis, icône verte
                        else if (operatorId && shiftDate && vacation) {
                            window.updateShiftIdStatusIcon('valid');
                        } 
                        // Si ID présent mais champs partiels, icône rouge
                        else {
                            window.updateShiftIdStatusIcon('partial');
                        }
                    }
                };
                
                // S'abonner aux changements des champs
                window.stateManager.subscribe('shift.operatorId', checkShiftFormStatus);
                window.stateManager.subscribe('shift.date', checkShiftFormStatus);
                window.stateManager.subscribe('shift.vacation', checkShiftFormStatus);
                
                // Afficher l'ID initial s'il existe déjà
                const currentId = window.stateManager.getState('shift.id');
                if (currentId) {
                    const shiftIdDisplay = document.getElementById('shift-id-display');
                    if (shiftIdDisplay) {
                        shiftIdDisplay.textContent = currentId;
                    }
                }
                
                // Vérifier l'état initial pour l'icône
                checkShiftFormStatus();
            }
        });
    }
});

// Fonction pour toggle le rouleau (utilisée dans le template)
window.toggleRouleau = function() {
    const qualityBlock = document.getElementById('quality-control-block');
    const chevron = document.querySelector('#rolls-container i[class*="bi-chevron"]');
    
    if (qualityBlock.style.display === 'none') {
        qualityBlock.style.display = 'flex';
        // Changer la classe pour chevron vers le bas
        chevron.classList.remove('bi-chevron-up');
        chevron.classList.add('bi-chevron-down');
    } else {
        qualityBlock.style.display = 'none';
        // Changer la classe pour chevron vers le haut
        chevron.classList.remove('bi-chevron-down');
        chevron.classList.add('bi-chevron-up');
    }
};