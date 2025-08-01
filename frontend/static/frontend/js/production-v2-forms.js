/**
 * Gestion des formulaires pour Production V2
 * - Opérateur (pour l'instant)
 * - OF en cours et découpe
 * - TODO: Ajouter les autres champs du shift plus tard
 */

// Fonction pour mettre à jour les informations de date
function updateDateInfo(dateStr) {
    const dateInfo = document.getElementById('date-info');
    if (!dateInfo || !dateStr) return;
    
    const date = new Date(dateStr);
    
    // Jours de la semaine abrégés en français
    const jours = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
    
    // Récupérer les infos
    const jourAbrege = jours[date.getDay()];
    
    // Calculer le numéro du jour dans l'année
    const startOfYear = new Date(date.getFullYear(), 0, 1);
    const diff = date - startOfYear;
    const numJourAnnee = Math.floor(diff / (24 * 60 * 60 * 1000)) + 1;
    
    // Calculer le numéro de semaine
    const days = Math.floor((date - startOfYear) / (24 * 60 * 60 * 1000));
    const numSemaine = Math.ceil((days + startOfYear.getDay() + 1) / 7);
    
    // Afficher
    dateInfo.textContent = `(${jourAbrege} | ${numJourAnnee} | S${numSemaine})`;
}

// ===== GESTION DU FORMULAIRE OPERATEUR =====
window.loadOperators = async function() {
    try {
        // Charger depuis le contexte Django d'abord (si disponible)
        if (window.operatorsData) {
            const select = document.getElementById('operator-select');
            window.operatorsData.forEach(op => {
                const option = document.createElement('option');
                option.value = op.employee_id;
                option.textContent = `${op.first_name} ${op.last_name}`;
                select.appendChild(option);
            });
            
            // Charger la valeur depuis la session
            const sessionData = await fetch('/api/session/').then(r => r.json());
            if (sessionData.operator_id) {
                select.value = sessionData.operator_id;
                select.classList.remove('v2-input');
                select.classList.add('v2-input-filled');
            }
            
            if (window.logDebug) logDebug('✅ Opérateurs chargés', 'success');
        } else {
            // Sinon charger depuis l'API
            const response = await fetch('/api/operators/');
            if (response.ok) {
                const operators = await response.json();
                const select = document.getElementById('operator-select');
                
                operators.forEach(op => {
                    const option = document.createElement('option');
                    option.value = op.employee_id;
                    option.textContent = `${op.first_name} ${op.last_name}`;
                    select.appendChild(option);
                });
                
                if (window.logDebug) logDebug('✅ Opérateurs chargés depuis API', 'success');
            } else {
                if (window.logDebug) logDebug('❌ Erreur chargement opérateurs', 'error');
            }
        }
    } catch (error) {
        if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
    }
};

// ===== GESTION DES OF =====
window.loadFabricationOrders = async function() {
    try {
        // Charger depuis le contexte Django d'abord
        if (window.fabricationOrdersData && window.cuttingOrdersData) {
            const ofSelect = document.getElementById('of-en-cours');
            const cuttingSelect = document.getElementById('of-decoupe');
            
            // Remplir OF en cours
            window.fabricationOrdersData.forEach(of => {
                const option = document.createElement('option');
                option.value = of.order_number;
                let text = of.order_number;
                if (of.required_length) {
                    text += ` (${of.required_length}m)`;
                }
                option.textContent = text;
                option.dataset.requiredLength = of.required_length || '';
                option.dataset.targetRollLength = of.target_roll_length || '';
                ofSelect.appendChild(option);
            });
            
            // Remplir OF de découpe
            window.cuttingOrdersData.forEach(of => {
                const option = document.createElement('option');
                option.value = of.order_number;
                option.textContent = of.order_number;
                cuttingSelect.appendChild(option);
            });
            
            // Charger les valeurs depuis la session
            const sessionData = await fetch('/api/session/').then(r => r.json());
            if (sessionData.of_en_cours) {
                ofSelect.value = sessionData.of_en_cours;
                ofSelect.classList.remove('v2-input');
                ofSelect.classList.add('v2-input-filled');
            }
            if (sessionData.target_length) {
                const longueurCibleInput = document.getElementById('longueur-cible');
                longueurCibleInput.value = sessionData.target_length;
                longueurCibleInput.classList.remove('v2-input');
                longueurCibleInput.classList.add('v2-input-filled');
                
                // Mettre à jour le StateManager
                if (window.stateManager) {
                    const numericValue = parseFloat(sessionData.target_length);
                    if (!isNaN(numericValue)) {
                        window.stateManager.setState('of.targetLength', numericValue, 'system');
                    }
                }
            }
            if (sessionData.of_decoupe) {
                cuttingSelect.value = sessionData.of_decoupe;
                cuttingSelect.classList.remove('v2-input');
                cuttingSelect.classList.add('v2-input-filled');
            }
            
            if (window.logDebug) logDebug('✅ OF chargés', 'success');
        } else {
            // Sinon charger depuis l'API
            const response = await fetch('/api/fabrication-orders/');
            if (response.ok) {
                const data = await response.json();
                const ofSelect = document.getElementById('of-en-cours');
                const cuttingSelect = document.getElementById('of-decoupe');
                
                // Remplir OF en cours
                data.fabrication_orders.forEach(of => {
                    const option = document.createElement('option');
                    option.value = of.order_number;
                    let text = of.order_number;
                    if (of.required_length) {
                        text += ` (${of.required_length}m)`;
                    }
                    option.textContent = text;
                    option.dataset.requiredLength = of.required_length || '';
                    option.dataset.targetRollLength = of.target_roll_length || '';
                    ofSelect.appendChild(option);
                });
                
                // Remplir OF de découpe
                data.cutting_orders.forEach(of => {
                    const option = document.createElement('option');
                    option.value = of.order_number;
                    option.textContent = of.order_number;
                    cuttingSelect.appendChild(option);
                });
                
                if (window.logDebug) logDebug('✅ OF chargés depuis API', 'success');
            } else {
                if (window.logDebug) logDebug('❌ Erreur chargement OF', 'error');
            }
        }
    } catch (error) {
        if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
    }
};

// Helper pour CSRF
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : window.CSRF_TOKEN || '';
}

// Attacher les event listeners au chargement
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOMContentLoaded - production-v2-forms.js');
    // Gérer le changement d'OF en cours
    const ofSelect = document.getElementById('of-en-cours');
    if (ofSelect) {
        ofSelect.addEventListener('change', async (e) => {
            const ofNumber = e.target.value;
            const selectedOption = e.target.options[e.target.selectedIndex];
            
            try {
                if (window.stateManager) {
                    // Utiliser StateManager
                    window.stateManager.setState('of.enCours', ofNumber || null, 'user');
                    
                    // Mettre à jour automatiquement la longueur cible SEULEMENT si elle est vide
                    const longueurCibleInput = document.getElementById('longueur-cible');
                    if (ofNumber && selectedOption.dataset.targetRollLength && !longueurCibleInput.value) {
                        const targetLength = parseFloat(selectedOption.dataset.targetRollLength);
                        longueurCibleInput.value = selectedOption.dataset.targetRollLength;
                        longueurCibleInput.classList.remove('v2-input');
                        longueurCibleInput.classList.add('v2-input-filled');
                        
                        // Mettre à jour dans StateManager
                        window.stateManager.setState('of.targetLength', targetLength, 'user');
                        window.stateManager.setState('of.longueurCible', targetLength, 'user');
                    }
                    
                    // Émettre via EventBus
                    if (window.eventBus) {
                        window.eventBus.emit('of-changed', { of_number: ofNumber });
                    }
                    
                    // Recalculer l'ID du rouleau
                    if (window.updateRollId) {
                        window.updateRollId();
                    }
                    
                    if (window.logDebug) logDebug(`✅ OF mis à jour dans StateManager: ${ofNumber}`, 'success');
                } else {
                    // Fallback sur l'ancienne méthode
                    const longueurCibleInput = document.getElementById('longueur-cible');
                    if (ofNumber && selectedOption.dataset.targetRollLength && !longueurCibleInput.value) {
                        longueurCibleInput.value = selectedOption.dataset.targetRollLength;
                        longueurCibleInput.classList.remove('v2-input');
                        longueurCibleInput.classList.add('v2-input-filled');
                    }
                    
                    const response = await fetch('/api/session/', {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            of_en_cours: ofNumber || null,
                            target_length: longueurCibleInput.value || null
                        })
                    });
                    
                    if (response.ok) {
                        if (window.logDebug) logDebug(`✅ OF sauvegardé: ${ofNumber}`, 'success');
                        
                        window.dispatchEvent(new CustomEvent('of-changed', {
                            detail: { of_number: ofNumber }
                        }));
                    }
                }
                
                // Mettre à jour le style
                if (ofNumber) {
                    e.target.classList.remove('v2-input');
                    e.target.classList.add('v2-input-filled');
                } else {
                    e.target.classList.remove('v2-input-filled');
                    e.target.classList.add('v2-input');
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le changement de longueur cible - juste mettre à jour le style sur input
    const longueurInput = document.getElementById('longueur-cible');
    if (longueurInput) {
        longueurInput.addEventListener('input', (e) => {
            const value = e.target.value;
            
            // Mettre à jour le style
            if (value) {
                e.target.classList.remove('v2-input');
                e.target.classList.add('v2-input-filled');
            } else {
                e.target.classList.remove('v2-input-filled');
                e.target.classList.add('v2-input');
            }
        });
        
        // Sauvegarder seulement sur blur
        longueurInput.addEventListener('blur', async (e) => {
            const value = e.target.value;
            
            try {
                if (window.stateManager) {
                    // Parser et sauvegarder la valeur
                    const numericValue = value ? parseFloat(value) : null;
                    if (numericValue && !isNaN(numericValue) && numericValue > 0) {
                        window.stateManager.setState('of.targetLength', numericValue, 'user');
                        
                        // Synchroniser immédiatement avec le backend
                        if (window.syncEngine) {
                            window.syncEngine.sync('of.targetLength', numericValue, 'normal', true);
                        }
                        
                        if (window.logDebug) logDebug(`✅ Longueur cible sauvegardée: ${numericValue}`, 'success');
                    }
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le changement d'OF de découpe
    const decoupeSelect = document.getElementById('of-decoupe');
    if (decoupeSelect) {
        decoupeSelect.addEventListener('change', async (e) => {
            const ofNumber = e.target.value;
            
            try {
                const response = await fetch('/api/session/', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        of_decoupe: ofNumber || null
                    })
                });
                
                if (response.ok) {
                    if (ofNumber) {
                        e.target.classList.remove('v2-input');
                        e.target.classList.add('v2-input-filled');
                    } else {
                        e.target.classList.remove('v2-input-filled');
                        e.target.classList.add('v2-input');
                    }
                    if (window.logDebug) logDebug(`✅ OF découpe sauvegardé: ${ofNumber}`, 'success');
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le changement d'opérateur
    const operatorSelect = document.getElementById('operator-select');
    if (operatorSelect) {
        operatorSelect.addEventListener('change', async (e) => {
            const operatorId = e.target.value;
            
            try {
                if (window.commandBus) {
                    // Utiliser CommandBus V2
                    await window.commandBus.execute('CHANGE_OPERATOR', { operatorId });
                    
                    if (window.logDebug) logDebug(`✅ Opérateur changé: ${operatorId}`, 'success');
                } else {
                    // Fallback sur l'ancienne méthode
                    const response = await fetch('/api/session/', {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            operator_id: operatorId || null
                        })
                    });
                    
                    if (response.ok) {
                        if (window.logDebug) logDebug(`✅ Opérateur sauvegardé: ${operatorId}`, 'success');
                        
                        // Émettre un événement pour les autres composants
                        window.dispatchEvent(new CustomEvent('operator-changed', {
                            detail: { operator_id: operatorId }
                        }));
                    }
                }
                
                // Mettre à jour le style
                if (operatorId) {
                    e.target.classList.remove('v2-input');
                    e.target.classList.add('v2-input-filled');
                } else {
                    e.target.classList.remove('v2-input-filled');
                    e.target.classList.add('v2-input');
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le changement de date
    const dateInput = document.getElementById('shift-date');
    if (dateInput) {
        dateInput.addEventListener('change', async (e) => {
            const date = e.target.value;
            
            // Mettre à jour l'affichage du jour/numéro/semaine
            updateDateInfo(date);
            
            try {
                if (window.commandBus) {
                    await window.commandBus.execute('CHANGE_SHIFT_DATE', { date });
                    if (window.logDebug) logDebug(`✅ Date changée: ${date}`, 'success');
                } else {
                    // Fallback sur l'ancienne méthode
                    const response = await fetch('/api/session/', {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            shift_date: date || null
                        })
                    });
                    
                    if (response.ok) {
                        if (window.logDebug) logDebug(`✅ Date sauvegardée: ${date}`, 'success');
                    }
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le changement de vacation
    const vacationSelect = document.getElementById('vacation');
    if (vacationSelect) {
        vacationSelect.addEventListener('change', async (e) => {
            const vacation = e.target.value;
            
            try {
                if (window.commandBus) {
                    await window.commandBus.execute('CHANGE_VACATION', { vacation });
                    if (window.logDebug) logDebug(`✅ Vacation changée: ${vacation}`, 'success');
                } else {
                    // Fallback sur l'ancienne méthode
                    const response = await fetch('/api/session/', {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            vacation: vacation || null
                        })
                    });
                    
                    if (response.ok) {
                        if (window.logDebug) logDebug(`✅ Vacation sauvegardée: ${vacation}`, 'success');
                    }
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer les champs de prise de poste
    const startTimeInput = document.getElementById('start-time');
    if (startTimeInput) {
        startTimeInput.addEventListener('change', async (e) => {
            const time = e.target.value;
            try {
                if (window.stateManager) {
                    window.stateManager.setState('shift.startTime', time);
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    const lengthStartInput = document.getElementById('length-start');
    if (lengthStartInput) {
        lengthStartInput.addEventListener('input', async (e) => {
            const length = e.target.value;
            try {
                if (window.stateManager) {
                    window.stateManager.setState('shift.lengthStart', length);
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer les champs de fin de poste
    const endTimeInput = document.getElementById('end-time');
    if (endTimeInput) {
        endTimeInput.addEventListener('change', async (e) => {
            const time = e.target.value;
            try {
                if (window.stateManager) {
                    window.stateManager.setState('shift.endTime', time);
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    const lengthEndInput = document.getElementById('length-end');
    if (lengthEndInput) {
        lengthEndInput.addEventListener('input', async (e) => {
            const length = e.target.value;
            try {
                if (window.stateManager) {
                    window.stateManager.setState('shift.lengthEnd', length);
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Gérer le champ commentaires
    const commentInput = document.getElementById('shift-comment');
    if (commentInput) {
        commentInput.addEventListener('input', async (e) => {
            const comment = e.target.value;
            try {
                if (window.stateManager) {
                    window.stateManager.setState('shift.comment', comment);
                }
            } catch (error) {
                if (window.logDebug) logDebug('❌ Erreur: ' + error.message, 'error');
            }
        });
    }
    
    // Charger les valeurs initiales depuis la session
    
    // Récupérer les éléments du shift
    const operatorSelectForLoad = document.getElementById('operator-select');
    const dateInputForLoad = document.getElementById('shift-date');
    const vacationSelectForLoad = document.getElementById('vacation');
    
    fetch('/api/session/')
        .then(r => r.json())
        .then(sessionData => {
            if (sessionData.operator_id && operatorSelectForLoad) {
                operatorSelectForLoad.value = sessionData.operator_id;
                operatorSelectForLoad.classList.remove('v2-input');
                operatorSelectForLoad.classList.add('v2-input-filled');
            }
            
            if (sessionData.shift_date && dateInputForLoad) {
                dateInputForLoad.value = sessionData.shift_date;
                dateInputForLoad.classList.remove('v2-input');
                dateInputForLoad.classList.add('v2-input-filled');
                console.log('✅ Date restaurée:', sessionData.shift_date);
            }
            
            if (sessionData.vacation && vacationSelectForLoad) {
                vacationSelectForLoad.value = sessionData.vacation;
                vacationSelectForLoad.classList.remove('v2-input');
                vacationSelectForLoad.classList.add('v2-input-filled');
                console.log('✅ Vacation restaurée:', sessionData.vacation);
            }
            
            // Charger les données de prise de poste
            const machineStartCheckbox = document.getElementById('machine-started-start');
            const startTimeForLoad = document.getElementById('start-time');
            const lengthStartForLoad = document.getElementById('length-start');
            
            if (sessionData.machine_started_start && machineStartCheckbox) {
                machineStartCheckbox.checked = sessionData.machine_started_start;
                // Déclencher la commande pour afficher les champs
                if (window.commandBus) {
                    window.commandBus.execute('CHANGE_MACHINE_START_STATE', { started: true });
                }
                
                if (sessionData.start_time && startTimeForLoad) {
                    startTimeForLoad.value = sessionData.start_time;
                }
                
                if (sessionData.length_start && lengthStartForLoad) {
                    lengthStartForLoad.value = sessionData.length_start;
                }
            }
            
            // Charger les données de fin de poste
            const machineEndCheckbox = document.getElementById('machine-started-end');
            const endTimeForLoad = document.getElementById('end-time');
            const lengthEndForLoad = document.getElementById('length-end');
            
            if (sessionData.machine_started_end && machineEndCheckbox) {
                machineEndCheckbox.checked = sessionData.machine_started_end;
                // Déclencher la commande pour afficher les champs
                if (window.commandBus) {
                    window.commandBus.execute('CHANGE_MACHINE_END_STATE', { started: true });
                }
                
                if (sessionData.end_time && endTimeForLoad) {
                    endTimeForLoad.value = sessionData.end_time;
                }
                
                if (sessionData.length_end && lengthEndForLoad) {
                    lengthEndForLoad.value = sessionData.length_end;
                }
            }
            
            // Charger le commentaire
            const commentForLoad = document.getElementById('shift-comment');
            if (sessionData.comment && commentForLoad) {
                commentForLoad.value = sessionData.comment;
            }
            
            // Utiliser les commandes pour charger les valeurs initiales
            if (window.commandBus) {
                if (sessionData.operator_id) {
                    window.commandBus.execute('CHANGE_OPERATOR', { operatorId: sessionData.operator_id });
                }
                if (sessionData.shift_date) {
                    window.commandBus.execute('CHANGE_SHIFT_DATE', { date: sessionData.shift_date });
                    updateDateInfo(sessionData.shift_date);
                }
                if (sessionData.vacation) {
                    window.commandBus.execute('CHANGE_VACATION', { vacation: sessionData.vacation });
                }
                
                // Si tous les champs sont remplis, forcer la génération de l'ID
                if (sessionData.operator_id && sessionData.shift_date && sessionData.vacation) {
                    console.log('📝 Tous les champs sont remplis, génération de l\'ID...');
                    setTimeout(async () => {
                        await window.commandBus.execute('GENERATE_SHIFT_ID', {
                            operatorId: sessionData.operator_id,
                            date: sessionData.shift_date,
                            vacation: sessionData.vacation
                        });
                        
                        // Forcer l'affichage de l'ID
                        const shiftId = window.stateManager.getState('shift.id');
                        if (shiftId) {
                            const shiftIdDisplay = document.getElementById('shift-id-display');
                            if (shiftIdDisplay) {
                                shiftIdDisplay.textContent = shiftId;
                            }
                            // Mettre à jour l'icône d'état
                            if (window.updateShiftIdStatusIcon) {
                                window.updateShiftIdStatusIcon('valid');
                            }
                        }
                    }, 100);
                }
            }
            
        })
        .catch(error => {
            if (window.logDebug) logDebug('❌ Erreur chargement session: ' + error.message, 'error');
        });
});