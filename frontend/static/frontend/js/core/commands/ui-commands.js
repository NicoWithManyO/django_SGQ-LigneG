/**
 * Commandes UI pour la gestion de l'interface utilisateur
 */

function registerUICommands(commandBus) {
    
    /**
     * Commande : Déverrouiller un champ
     */
    commandBus.register(
        'UNLOCK_FIELD',
        async (payload, state) => {
            const { fieldId } = payload;
            
            // Mettre à jour l'état
            state.setState(`ui.locks.${fieldId}`, false);
            
            // Retourner les infos pour l'effet UI
            return {
                fieldId,
                locked: false,
                timestamp: Date.now()
            };
        },
        // Validateur
        (payload) => {
            if (!payload.fieldId) {
                return {
                    valid: false,
                    errors: ['fieldId requis']
                };
            }
            return { valid: true, errors: [] };
        },
        // Effets
        [
            (result) => {
                // Émettre l'événement pour que le composant UI réagisse
                window.eventBus.emit('field:unlocked', result);
            }
        ]
    );
    
    /**
     * Commande : Verrouiller un champ
     */
    commandBus.register(
        'LOCK_FIELD',
        async (payload, state) => {
            const { fieldId, value } = payload;
            
            // Mettre à jour l'état
            state.setState(`ui.locks.${fieldId}`, true);
            
            // Si une valeur est fournie, la sauvegarder aussi
            if (value !== undefined) {
                // Déterminer le chemin de stockage selon le fieldId
                const fieldPaths = {
                    'of-en-cours': 'of.enCours',
                    'longueur-cible': 'of.targetLength',
                    'of-decoupe': 'of.decoupe'
                };
                
                const statePath = fieldPaths[fieldId];
                if (statePath) {
                    state.setState(statePath, value);
                }
            }
            
            return {
                fieldId,
                locked: true,
                value,
                timestamp: Date.now()
            };
        },
        null,
        [
            (result) => {
                // Émettre l'événement
                window.eventBus.emit('field:locked', result);
            }
        ]
    );
    
    /**
     * Commande : Basculer l'état de verrouillage
     */
    commandBus.register(
        'TOGGLE_FIELD_LOCK',
        async (payload, state) => {
            const { fieldId } = payload;
            const currentLocked = state.getState(`ui.locks.${fieldId}`, true);
            
            // Exécuter la commande appropriée
            if (currentLocked) {
                return await commandBus.execute('UNLOCK_FIELD', { fieldId });
            } else {
                return await commandBus.execute('LOCK_FIELD', { fieldId });
            }
        }
    );
    
    /**
     * Commande : Déverrouiller temporairement un champ
     */
    commandBus.register(
        'UNLOCK_FIELD_TEMPORARILY',
        async (payload, state) => {
            const { fieldId, duration = 5000 } = payload;
            
            // Déverrouiller
            await commandBus.execute('UNLOCK_FIELD', { fieldId });
            
            // Programmer le reverrouillage
            setTimeout(() => {
                const element = document.getElementById(fieldId);
                if (element && !element.matches(':focus')) {
                    commandBus.execute('LOCK_FIELD', { 
                        fieldId,
                        value: element.value 
                    });
                }
            }, duration);
            
            return { fieldId, duration };
        }
    );
    
    /**
     * Commande : Initialiser l'état de verrouillage
     */
    commandBus.register(
        'INIT_FIELD_LOCKS',
        async (payload, state) => {
            const { fields } = payload;
            
            // Initialiser l'état de verrouillage pour chaque champ
            fields.forEach(fieldId => {
                const currentState = state.getState(`ui.locks.${fieldId}`);
                if (currentState === undefined) {
                    state.setState(`ui.locks.${fieldId}`, true);
                }
            });
            
            return { fields, initialized: true };
        }
    );
    
    /**
     * Commande : Restaurer l'état UI (checkboxes et champs)
     */
    commandBus.register(
        'RESTORE_UI_STATE',
        (payload, state) => {
            console.log('🔄 Restauration de l\'état UI...');
            
            // Machine started début
            const machineStartedStart = state.getState('shift.machineStartedStart');
            if (machineStartedStart) {
                const checkbox = document.getElementById('machine-started-start');
                if (checkbox) {
                    checkbox.checked = true;
                    // Afficher les champs
                    const lengthInput = document.getElementById('length-start');
                    if (lengthInput) {
                        lengthInput.style.display = '';
                    }
                }
            }
            
            // Machine started fin
            const machineStartedEnd = state.getState('shift.machineStartedEnd');
            if (machineStartedEnd) {
                const checkbox = document.getElementById('machine-started-end');
                if (checkbox) {
                    checkbox.checked = true;
                    // Afficher les champs
                    const lengthInput = document.getElementById('length-end');
                    if (lengthInput) {
                        lengthInput.style.display = '';
                    }
                }
            }
            
            // Longueurs
            const lengthStart = state.getState('shift.lengthStart');
            if (lengthStart) {
                const input = document.getElementById('length-start');
                if (input) {
                    input.value = lengthStart;
                }
            }
            
            const lengthEnd = state.getState('shift.lengthEnd');
            if (lengthEnd) {
                const input = document.getElementById('length-end');
                if (input) {
                    input.value = lengthEnd;
                }
            }
            
            // Restaurer les épaisseurs dans la grille - EXACTEMENT COMME LES LONGUEURS
            const thicknesses = state.getState('production.currentRoll.thicknesses');
            if (thicknesses && Object.keys(thicknesses).length > 0) {
                // Attendre un peu que la grille soit rendue
                setTimeout(() => {
                    Object.entries(thicknesses).forEach(([key, value]) => {
                        const [row, col] = key.split('-');
                        const input = document.getElementById(`thickness-${row}-${col}`);
                        if (input) {
                            input.value = value;
                            input.classList.add('v2-input-filled');
                        }
                    });
                }, 1000);
            }
            
            return { restored: true };
        }
    );
}

// Exposer globalement
window.registerUICommands = registerUICommands;