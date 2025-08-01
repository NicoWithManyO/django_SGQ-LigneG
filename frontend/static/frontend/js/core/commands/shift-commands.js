/**
 * Commandes métier pour la gestion des postes (shifts)
 */

// Fonction de génération d'ID inline pour éviter les problèmes d'import
function generateShiftId(operatorId, shiftDate, vacation) {
    console.log('🔍 generateShiftId called:', { operatorId, shiftDate, vacation });
    
    if (!operatorId || !shiftDate || !vacation) {
        console.log('❌ Missing data for ID generation');
        return null;
    }
    
    // Formater la date
    const date = new Date(shiftDate);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    const dateStr = `${day}${month}${year}`;
    
    // Récupérer le nom de l'opérateur
    let operatorName = '';
    
    // Essayer depuis le DOM
    const operatorSelect = document.getElementById('operator-select');
    if (operatorSelect) {
        const selectedOption = operatorSelect.querySelector(`option[value="${operatorId}"]`);
        if (selectedOption) {
            const fullName = selectedOption.textContent.trim();
            const nameParts = fullName.split(' ');
            const firstName = nameParts[0] || '';
            const lastName = nameParts.slice(1).join('') || '';
            // Format uniforme : PrenomNom avec première lettre du nom en majuscule
            operatorName = firstName + lastName.charAt(0).toUpperCase() + lastName.slice(1).toLowerCase();
        }
    }
    
    // Sinon essayer depuis les données globales
    if (!operatorName && window.operatorsData) {
        const operator = window.operatorsData.find(op => op.employee_id === operatorId);
        if (operator) {
            // Format: PrenomNom avec première lettre du nom en majuscule seulement
            operatorName = operator.first_name + operator.last_name.charAt(0).toUpperCase() + operator.last_name.slice(1).toLowerCase();
        }
    }
    
    if (!operatorName) {
        console.log('❌ Pas de nom d\'opérateur trouvé');
        return null;
    }
    
    
    return `${dateStr}_${operatorName}_${vacation}`;
}

function registerShiftCommands(commandBus) {
    
    /**
     * Commande : Changer d'opérateur
     */
    commandBus.register(
        'CHANGE_OPERATOR',
        async (payload, state) => {
            const { operatorId } = payload;
            
            // Mettre à jour l'état
            state.setState('shift.operatorId', operatorId || null);
            
            // Récupérer les données nécessaires pour l'ID
            const shiftDate = state.getState('shift.date');
            const vacation = state.getState('shift.vacation');
            
            // Générer le nouvel ID si toutes les données sont présentes
            if (operatorId && shiftDate && vacation) {
                const shiftId = generateShiftId(operatorId, shiftDate, vacation);
                state.setState('shift.id', shiftId);
                
                // Pour l'instant, on considère que l'ID est valide
                state.setState('shift.idStatus', 'valid');
            }
            // Ne PAS mettre l'ID à null si on n'a pas toutes les données
            // Garder l'ancien ID jusqu'à ce qu'on puisse en générer un nouveau
            
            return { operatorId };
        },
        // Pas de validateur, on accepte les valeurs vides
        null,
        // Effets
        [
            // Reset checklist
            (result, payload, state) => {
                state.setState('checklist.responses', {});
                state.setState('checklist.signed', false);
                state.setState('checklist.signatureTime', null);
            },
            // Emit event
            (result) => {
                window.eventBus.emit('operator-changed', result);
            }
        ]
    );
    
    /**
     * Commande : Changer la date du poste
     */
    commandBus.register(
        'CHANGE_SHIFT_DATE',
        async (payload, state) => {
            const { date } = payload;
            
            state.setState('shift.date', date);
            
            // Regénérer l'ID si nécessaire
            const operatorId = state.getState('shift.operatorId');
            const vacation = state.getState('shift.vacation');
            
            if (operatorId && date && vacation) {
                await commandBus.execute('GENERATE_SHIFT_ID', {
                    operatorId,
                    date,
                    vacation
                });
            }
            
            return { date };
        }
    );
    
    /**
     * Commande : Changer la vacation
     */
    commandBus.register(
        'CHANGE_VACATION',
        async (payload, state) => {
            const { vacation } = payload;
            
            state.setState('shift.vacation', vacation);
            
            // Définir les heures par défaut selon la vacation
            const defaultHours = {
                'Matin': { start: '04:00', end: '12:00' },
                'ApresMidi': { start: '12:00', end: '20:00' },
                'Nuit': { start: '20:00', end: '04:00' },
                'Journee': { start: '07:30', end: '15:30' }
            };
            
            if (defaultHours[vacation]) {
                state.setState('shift.startTime', defaultHours[vacation].start);
                state.setState('shift.endTime', defaultHours[vacation].end);
                
                // Mettre à jour les champs visuellement
                const startTimeInput = document.getElementById('start-time');
                const endTimeInput = document.getElementById('end-time');
                
                if (startTimeInput) {
                    startTimeInput.value = defaultHours[vacation].start;
                }
                if (endTimeInput) {
                    endTimeInput.value = defaultHours[vacation].end;
                }
            }
            
            // Regénérer l'ID
            const operatorId = state.getState('shift.operatorId');
            const date = state.getState('shift.date');
            
            if (operatorId && date && vacation) {
                await commandBus.execute('GENERATE_SHIFT_ID', {
                    operatorId,
                    date,
                    vacation
                });
            }
            
            return { vacation, hours: defaultHours[vacation] };
        }
    );
    
    /**
     * Commande : Générer l'ID du poste
     */
    commandBus.register(
        'GENERATE_SHIFT_ID',
        async (payload, state) => {
            const { operatorId, date, vacation } = payload;
            console.log('📌 GENERATE_SHIFT_ID appelée avec:', { operatorId, date, vacation });
            
            const shiftId = generateShiftId(operatorId, date, vacation);
            
            state.setState('shift.id', shiftId);
            
            // Pour l'instant, on considère que l'ID est valide
            state.setState('shift.idStatus', shiftId ? 'valid' : 'empty');
            
            return { shiftId };
        }
    );
    
    /**
     * Commande : Changer l'état machine début
     */
    commandBus.register(
        'CHANGE_MACHINE_START_STATE',
        (payload, state) => {
            const { started } = payload;
            console.log('🔄 CHANGE_MACHINE_START_STATE:', started);
            
            state.setState('shift.machineStartedStart', started, 'user');
            
            // Si machine non démarrée, effacer la longueur
            if (!started) {
                state.setState('shift.lengthStart', '', 'user');
                state.setState('shift.startTime', '', 'user');
            }
            
            // Afficher/cacher le champ longueur uniquement
            const lengthInput = document.getElementById('length-start');
            if (lengthInput) {
                lengthInput.style.display = started ? 'block' : 'none';
            }
            
            // Valider le formulaire
            window.eventBus.emit('shift:validate');
            
            return { started };
        }
    );
    
    /**
     * Commande : Changer l'état machine fin
     */
    commandBus.register(
        'CHANGE_MACHINE_END_STATE',
        (payload, state) => {
            const { started } = payload;
            
            state.setState('shift.machineStartedEnd', started, 'user');
            
            // Si machine non démarrée, effacer la longueur
            if (!started) {
                state.setState('shift.lengthEnd', '', 'user');
                state.setState('shift.endTime', '', 'user');
            }
            
            // Afficher/cacher le champ longueur uniquement
            const lengthInput = document.getElementById('length-end');
            if (lengthInput) {
                lengthInput.style.display = started ? 'block' : 'none';
            }
            
            // Valider le formulaire
            window.eventBus.emit('shift:validate');
            
            return { started };
        }
    );
    
    /**
     * Commande : Changer la longueur début
     */
    commandBus.register(
        'CHANGE_LENGTH_START',
        (payload, state) => {
            const { length } = payload;
            state.setState('shift.lengthStart', length, 'user');
            return { lengthStart: length };
        }
    );
    
    /**
     * Commande : Changer la longueur fin
     */
    commandBus.register(
        'CHANGE_LENGTH_END',
        (payload, state) => {
            const { length } = payload;
            state.setState('shift.lengthEnd', length, 'user');
            return { lengthEnd: length };
        }
    );
    
    /**
     * Commande : Récupérer la longueur du dernier poste
     */
    commandBus.register(
        'FETCH_LAST_SHIFT_LENGTH',
        async (payload, state) => {
            try {
                const response = await window.apiV2.get('/api/shifts/last/');
                
                if (response && response.wound_length_end) {
                    state.setState('shift.lengthStart', response.wound_length_end.toString());
                    state.setState('shift.machineStartedStart', true);
                    
                    return {
                        success: true,
                        length: response.wound_length_end,
                        shiftId: response.shift_id
                    };
                }
                
                return {
                    success: false,
                    message: 'Aucun poste précédent trouvé'
                };
            } catch (error) {
                console.error('Error fetching last shift:', error);
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    );
    
    /**
     * Commande : Valider le poste complet
     */
    commandBus.register(
        'VALIDATE_SHIFT',
        (payload, state) => {
            const errors = [];
            
            // Récupérer toutes les données nécessaires
            const shiftData = {
                id: state.getState('shift.id'),
                idStatus: state.getState('shift.idStatus'),
                operatorId: state.getState('shift.operatorId'),
                date: state.getState('shift.date'),
                vacation: state.getState('shift.vacation'),
                startTime: state.getState('shift.startTime'),
                endTime: state.getState('shift.endTime'),
                machineStartedStart: state.getState('shift.machineStartedStart'),
                machineStartedEnd: state.getState('shift.machineStartedEnd'),
                lengthStart: state.getState('shift.lengthStart'),
                lengthEnd: state.getState('shift.lengthEnd'),
                qcStatus: state.getState('qc.status'),
                checklistSigned: state.getState('checklist.signed'),
                hasStartupTime: state.getState('lostTime.hasStartupTime')
            };
            
            // Validations de base
            if (!shiftData.id) errors.push('ID du poste manquant');
            if (shiftData.idStatus === 'duplicate') errors.push('Cet ID de poste existe déjà');
            if (!shiftData.operatorId) errors.push('Sélectionner un opérateur');
            if (!shiftData.date) errors.push('Saisir la date');
            if (!shiftData.vacation) errors.push('Sélectionner la vacation');
            if (!shiftData.startTime) errors.push('Saisir l\'heure de début');
            if (!shiftData.endTime) errors.push('Saisir l\'heure de fin');
            
            // Validation contrôle qualité
            if (shiftData.qcStatus === 'pending') {
                errors.push('Compléter le contrôle qualité');
            }
            
            // Validation checklist
            if (!shiftData.checklistSigned) {
                errors.push('Signer la checklist de démarrage');
            }
            
            // Validation temps de démarrage
            if (!shiftData.machineStartedStart && !shiftData.hasStartupTime) {
                errors.push('Déclarer le temps de démarrage machine');
            }
            
            // Validation cohérence machine/métrage
            if (shiftData.machineStartedStart && !shiftData.lengthStart) {
                errors.push('Saisir le métrage de début (machine démarrée)');
            }
            
            if (shiftData.machineStartedEnd && !shiftData.lengthEnd) {
                errors.push('Saisir le métrage de fin (machine démarrée)');
            }
            
            // Validation cohérence des heures (sauf vacation Nuit)
            if (shiftData.vacation !== 'Nuit' && shiftData.startTime && shiftData.endTime) {
                const startMinutes = timeToMinutes(shiftData.startTime);
                const endMinutes = timeToMinutes(shiftData.endTime);
                
                if (startMinutes >= endMinutes) {
                    errors.push('L\'heure de fin doit être après l\'heure de début');
                }
            }
            
            const isValid = errors.length === 0;
            
            state.setState('shift.isValid', isValid);
            state.setState('shift.validationErrors', errors);
            
            return {
                valid: isValid,
                errors,
                data: shiftData
            };
        }
    );
    
    /**
     * Commande : Sauvegarder le poste
     */
    commandBus.register(
        'SAVE_SHIFT',
        async (payload, state) => {
            // Valider d'abord
            const validation = await commandBus.execute('VALIDATE_SHIFT');
            
            if (!validation.valid) {
                throw new Error(validation.errors.join(', '));
            }
            
            // Préparer les données pour l'API
            const shiftData = {
                date: state.getState('shift.date'),
                operator: state.getState('shift.operatorId'),
                vacation: state.getState('shift.vacation'),
                start_time: state.getState('shift.startTime'),
                end_time: state.getState('shift.endTime'),
                started_at_beginning: state.getState('shift.machineStartedStart'),
                meter_reading_start: state.getState('shift.machineStartedStart') ? 
                    parseFloat(state.getState('shift.lengthStart')) || null : null,
                started_at_end: state.getState('shift.machineStartedEnd'),
                meter_reading_end: state.getState('shift.machineStartedEnd') ? 
                    parseFloat(state.getState('shift.lengthEnd')) || null : null,
                operator_comments: state.getState('shift.comment') || ''
            };
            
            // Sauvegarder via l'API
            const response = await window.apiV2.post('/api/shifts/', shiftData);
            
            if (!response || !response.id) {
                throw new Error('Erreur lors de la sauvegarde du poste');
            }
            
            // Émettre l'événement de succès
            window.eventBus.emit('shift:saved', {
                shift: response
            });
            
            return response;
        },
        // Validateur
        null,
        // Effets
        [
            // Préparer le prochain poste si données disponibles
            async (result, payload, state) => {
                if (result.next_shift_data) {
                    // Sauvegarder les données du prochain poste
                    await window.apiV2.saveToSession(result.next_shift_data);
                }
            }
        ]
    );
}

// Fonction utilitaire
function timeToMinutes(time) {
    if (!time) return 0;
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
}

// Fonction pour mettre à jour l'icône d'état de l'ID
function updateShiftIdStatusIcon(status) {
    const icon = document.getElementById('shift-id-status-icon');
    if (!icon) return;
    
    // Retirer toutes les classes d'état
    icon.classList.remove('bi-check-circle', 'bi-x-circle', 'bi-dash-circle', 
                         'text-success', 'text-danger', 'text-muted');
    
    switch (status) {
        case 'valid':
            icon.classList.add('bi-check-circle', 'text-success');
            break;
        case 'partial':
            icon.classList.add('bi-x-circle', 'text-danger');
            break;
        case 'empty':
        default:
            icon.classList.add('bi-dash-circle', 'text-muted');
            break;
    }
}

// Exposer globalement
window.registerShiftCommands = registerShiftCommands;
window.generateShiftId = generateShiftId; // Pour debug
window.updateShiftIdStatusIcon = updateShiftIdStatusIcon; // Pour mise à jour externe
