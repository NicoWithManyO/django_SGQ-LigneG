/**
 * Commandes métier pour la gestion des rouleaux
 */

// Fonctions de génération d'ID inline
function generateRollId(ofNumber, rollNumber) {
    if (!ofNumber || rollNumber == null) {
        return null;
    }
    
    const paddedNumber = String(rollNumber).padStart(3, '0');
    return `${ofNumber}_${paddedNumber}`;
}

function generateCuttingRollId(cuttingOrderNumber, forDisplay = false) {
    if (!cuttingOrderNumber) {
        return null;
    }
    
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = String(now.getFullYear()).slice(-2);
    
    if (forDisplay) {
        return `${cuttingOrderNumber}_${day}${month}${year}`;
    } else {
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        return `${cuttingOrderNumber}_${day}${month}${year}_${hours}${minutes}`;
    }
}

function registerRollCommands(commandBus) {
    
    /**
     * Commande : Changer le numéro de rouleau
     */
    commandBus.register(
        'CHANGE_ROLL_NUMBER',
        async (payload, state) => {
            const { rollNumber } = payload;
            
            
            // Mettre à jour le numéro de rouleau avec source 'user' pour déclencher la sync
            state.setState('production.currentRollNumber', rollNumber, 'user');
            
            // Récupérer l'OF en cours
            const ofNumber = state.getState('of.enCours');
            
            if (ofNumber && rollNumber) {
                // Générer l'ID du rouleau
                const rollId = generateRollId(ofNumber, rollNumber);
                    
                // Mettre à jour l'ID avec source 'user' pour déclencher la sync
                state.setState('production.currentRollId', rollId, 'user');
                
                // Mettre à jour les affichages
                if (window.updateRollId) {
                    window.updateRollId();
                }
                
                // Forcer une synchronisation immédiate
                if (window.syncEngine) {
                        window.syncEngine.syncNow();
                }
                
                return { rollNumber, rollId };
            } else {
                console.log('⚠️ Cannot generate roll ID - OF:', ofNumber, 'Roll:', rollNumber);
            }
            
            return { rollNumber, rollId: null };
        }
    );
    
    /**
     * Commande : Auto-incrémenter le numéro de rouleau
     */
    commandBus.register(
        'AUTO_INCREMENT_ROLL_NUMBER',
        async (payload, state) => {
            // Récupérer le numéro actuel
            const currentNumber = state.getState('production.currentRollNumber') || 0;
            const nextNumber = parseInt(currentNumber) + 1;
            
            // Mettre à jour le champ visuellement
            const rollNumberField = document.getElementById('roll-number');
            if (rollNumberField) {
                // Si le champ est verrouillé, le déverrouiller d'abord
                if (rollNumberField.readOnly) {
                    rollNumberField.readOnly = false;
                    rollNumberField.classList.remove('v2-input-locked');
                    rollNumberField.classList.add('v2-input');
                    rollNumberField.style.cursor = 'pointer';
                }
                rollNumberField.value = String(nextNumber).padStart(3, '0');
            }
            
            // Utiliser la commande CHANGE_ROLL_NUMBER
            return await commandBus.execute('CHANGE_ROLL_NUMBER', {
                rollNumber: nextNumber
            });
        }
    );
    
    /**
     * Commande : Créer un nouveau rouleau
     */
    commandBus.register(
        'CREATE_ROLL',
        async (payload, state) => {
            const { ofNumber, rollNumber, targetLength } = payload;
            
            // Générer l'ID du rouleau
            const rollId = generateRollId(ofNumber, rollNumber);
            
            // Créer le rouleau dans l'état
            const roll = {
                id: rollId,
                ofNumber,
                rollNumber,
                targetLength,
                createdAt: Date.now(),
                status: 'active',
                thicknesses: [],
                defects: [],
                conformity: true
            };
            
            // Ajouter à la liste des rouleaux
            const rolls = state.getState('production.rolls', []);
            rolls.push(roll);
            state.setState('production.rolls', rolls);
            
            // Définir comme rouleau actuel
            state.setState('production.currentRoll', roll);
            state.setState('production.currentRollId', rollId);
            
            return roll;
        },
        // Validateur
        (payload) => {
            const errors = [];
            
            if (!payload.ofNumber) errors.push('Numéro OF requis');
            if (payload.rollNumber == null) errors.push('Numéro de rouleau requis');
            if (!payload.targetLength || payload.targetLength <= 0) {
                errors.push('Longueur cible requise et doit être positive');
            }
            
            return {
                valid: errors.length === 0,
                errors
            };
        },
        // Effets
        [
            // Émettre l'événement de création
            (result) => {
                window.eventBus.emit('roll:created', result);
            }
        ]
    );
    
    /**
     * Commande : Mettre à jour les mesures du rouleau
     */
    commandBus.register(
        'UPDATE_ROLL_MEASUREMENTS',
        (payload, state) => {
            const { rollId, totalMass, tubeMass, length } = payload;
            
            // Récupérer le rouleau
            const rolls = state.getState('production.rolls', []);
            const rollIndex = rolls.findIndex(r => r.id === rollId);
            
            if (rollIndex === -1) {
                throw new Error('Rouleau non trouvé');
            }
            
            const roll = { ...rolls[rollIndex] };
            
            // Mettre à jour les mesures
            if (totalMass !== undefined) roll.totalMass = totalMass;
            if (tubeMass !== undefined) roll.tubeMass = tubeMass;
            if (length !== undefined) roll.length = length;
            
            // Calculer la masse nette et le grammage
            if (roll.totalMass && roll.tubeMass && roll.totalMass > roll.tubeMass) {
                roll.netMass = roll.totalMass - roll.tubeMass;
                
                if (roll.length && roll.length > 0) {
                    const feltWidth = state.getState('production.currentProfile.feltWidth', 1);
                    const surface = roll.length * feltWidth;
                    roll.grammage = (roll.netMass / surface).toFixed(1);
                }
            }
            
            // Mettre à jour dans l'état
            rolls[rollIndex] = roll;
            state.setState('production.rolls', rolls);
            
            if (state.getState('production.currentRollId') === rollId) {
                state.setState('production.currentRoll', roll);
            }
            
            return roll;
        }
    );
    
    /**
     * Commande : Ajouter une épaisseur au rouleau
     */
    commandBus.register(
        'ADD_ROLL_THICKNESS',
        (payload, state) => {
            const { rollId, row, col, value, position } = payload;
            
            // Récupérer le rouleau
            const rolls = state.getState('production.rolls', []);
            const rollIndex = rolls.findIndex(r => r.id === rollId);
            
            if (rollIndex === -1) {
                throw new Error('Rouleau non trouvé');
            }
            
            const roll = { ...rolls[rollIndex] };
            
            // Récupérer les spécifications d'épaisseur
            const thicknessSpec = state.getState('production.currentProfile.specs.thickness', {});
            
            // Valider l'épaisseur
            const validation = window.validationEngine.validate('thickness.value', value, {
                spec: thicknessSpec
            });
            
            // Ajouter l'épaisseur
            const thickness = {
                row,
                col,
                value: parseFloat(value),
                position,
                isNok: !validation.valid || validation.warnings.length > 0,
                timestamp: Date.now()
            };
            
            if (!roll.thicknesses) roll.thicknesses = [];
            
            // Remplacer si existe déjà à cette position
            const existingIndex = roll.thicknesses.findIndex(
                t => t.row === row && t.col === col
            );
            
            if (existingIndex > -1) {
                roll.thicknesses[existingIndex] = thickness;
            } else {
                roll.thicknesses.push(thickness);
            }
            
            // Recalculer la conformité
            roll.conformity = calculateRollConformity(roll);
            
            // Mettre à jour dans l'état
            rolls[rollIndex] = roll;
            state.setState('production.rolls', rolls);
            
            if (state.getState('production.currentRollId') === rollId) {
                state.setState('production.currentRoll', roll);
            }
            
            return { roll, thickness, validation };
        }
    );
    
    /**
     * Commande : Ajouter/Mettre à jour une mesure d'épaisseur (pour la grille)
     */
    commandBus.register(
        'ADD_THICKNESS_MEASUREMENT',
        (payload, state) => {
            const { row, col, value } = payload;
            
            // S'assurer que production.currentRoll existe
            let currentRoll = state.getState('production.currentRoll');
            if (!currentRoll) {
                currentRoll = { thicknesses: {} };
                state.setState('production.currentRoll', currentRoll, 'system');
            }
            
            // S'assurer que thicknesses existe
            if (!currentRoll.thicknesses) {
                currentRoll.thicknesses = {};
            }
            
            const key = `${row}-${col}`;
            
            if (value === null || value === undefined || value === '') {
                // Supprimer la mesure
                delete currentRoll.thicknesses[key];
            } else {
                // Ajouter/mettre à jour la mesure
                currentRoll.thicknesses[key] = parseFloat(value);
            }
            
            // Mettre à jour l'état avec source 'user' pour déclencher la sync
            state.setState('production.currentRoll.thicknesses', currentRoll.thicknesses, 'user');
            
            // Forcer la synchronisation immédiate
            if (window.syncEngine) {
                window.syncEngine.sync('production.currentRoll.thicknesses', currentRoll.thicknesses, 'normal', true);
            }
            
            return { 
                row, 
                col, 
                value, 
                thicknesses: currentRoll.thicknesses 
            };
        }
    );
    
    /**
     * Commande : Supprimer une mesure d'épaisseur
     */
    commandBus.register(
        'REMOVE_THICKNESS_MEASUREMENT',
        (payload, state) => {
            const { row, col } = payload;
            
            return commandBus.execute('ADD_THICKNESS_MEASUREMENT', {
                row,
                col,
                value: null
            });
        }
    );
    
    /**
     * Commande : Calculer les statistiques d'épaisseur
     */
    commandBus.register(
        'CALCULATE_THICKNESS_STATS',
        (payload, state) => {
            const currentRoll = state.getState('production.currentRoll');
            if (!currentRoll || !currentRoll.thicknesses) {
                return {
                    count: 0,
                    min: null,
                    max: null,
                    avg: null,
                    stdDev: null
                };
            }
            
            const values = Object.values(currentRoll.thicknesses).filter(v => v != null);
            
            if (values.length === 0) {
                return {
                    count: 0,
                    min: null,
                    max: null,
                    avg: null,
                    stdDev: null
                };
            }
            
            const count = values.length;
            const min = Math.min(...values);
            const max = Math.max(...values);
            const sum = values.reduce((a, b) => a + b, 0);
            const avg = sum / count;
            
            // Calculer l'écart-type
            const squaredDiffs = values.map(v => Math.pow(v - avg, 2));
            const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / count;
            const stdDev = Math.sqrt(avgSquaredDiff);
            
            const stats = {
                count,
                min,
                max,
                avg: parseFloat(avg.toFixed(2)),
                stdDev: parseFloat(stdDev.toFixed(2))
            };
            
            // Sauvegarder les stats
            state.setState('roll.thicknessStats', stats, 'system');
            
            return stats;
        }
    );
    
    /**
     * Commande : Ajouter un défaut au rouleau
     */
    commandBus.register(
        'ADD_DEFECT',
        async (payload, state) => {
            const { row, col, defectId, defectName, severity } = payload;
            
            console.log('ADD_DEFECT appelé avec:', { row, col, defectId, defectName, severity });
            
            try {
                // S'assurer que production.currentRoll existe
                let currentRoll = state.getState('production.currentRoll');
                if (!currentRoll) {
                    currentRoll = { defects: {} };
                    state.setState('production.currentRoll', currentRoll, 'system');
                }
                
                // S'assurer que defects existe
                if (!currentRoll.defects) {
                    currentRoll.defects = {};
                }
                
                // Clé pour le défaut basée sur row-col
                const key = `${row}-${col}`;
                
                // Si un défaut existe déjà à cette position, le supprimer
                if (currentRoll.defects[key]) {
                    delete currentRoll.defects[key];
                    console.log(`Défaut supprimé à la position ${key}`);
                } else {
                    // Ajouter le nouveau défaut
                    currentRoll.defects[key] = {
                        id: defectId,
                        name: defectName,
                        severity: severity || 'normal',
                        timestamp: Date.now()
                    };
                    console.log(`Défaut ajouté à la position ${key}:`, currentRoll.defects[key]);
                }
                
                // Mettre à jour l'état avec source 'user' pour déclencher la sync
                state.setState('production.currentRoll.defects', currentRoll.defects, 'user');
                
                // Forcer la synchronisation immédiate
                if (window.syncEngine) {
                    window.syncEngine.sync('production.currentRoll.defects', currentRoll.defects, 'normal', true);
                }
                
                // Mettre à jour les compteurs de défauts
                const defectCounts = {};
                Object.values(currentRoll.defects).forEach(defect => {
                    defectCounts[defect.id] = (defectCounts[defect.id] || 0) + 1;
                });
                state.setState('roll.defectCounts', defectCounts, 'user');
                
                // Vérifier la conformité du rouleau - Attendre pour éviter les erreurs
                setTimeout(() => {
                    commandBus.execute('CHECK_ROLL_CONFORMITY').catch(err => {
                        console.error('Erreur CHECK_ROLL_CONFORMITY:', err);
                    });
                }, 10);
                
                return { 
                    row, 
                    col, 
                    defects: currentRoll.defects,
                    defectCounts
                };
            } catch (error) {
                console.error('Erreur dans ADD_DEFECT:', error);
                throw error;
            }
        },
        // Validateur
        (payload) => {
            const errors = [];
            
            if (payload.row == null) errors.push('Ligne requise');
            if (payload.col == null) errors.push('Colonne requise');
            if (!payload.defectId) errors.push('ID du défaut requis');
            if (!payload.defectName) errors.push('Nom du défaut requis');
            
            return {
                valid: errors.length === 0,
                errors
            };
        }
    );
    
    /**
     * Commande : Supprimer un défaut
     */
    commandBus.register(
        'REMOVE_DEFECT',
        (payload, state) => {
            const { row, col } = payload;
            
            // Récupérer le rouleau actuel
            const currentRoll = state.getState('production.currentRoll');
            if (!currentRoll || !currentRoll.defects) {
                return { row, col, defects: {} };
            }
            
            const key = `${row}-${col}`;
            
            // Supprimer le défaut
            if (currentRoll.defects[key]) {
                delete currentRoll.defects[key];
                
                // Mettre à jour l'état
                state.setState('production.currentRoll.defects', currentRoll.defects, 'user');
                
                // Forcer la synchronisation
                if (window.syncEngine) {
                    window.syncEngine.sync('production.currentRoll.defects', currentRoll.defects, 'normal', true);
                }
                
                // Mettre à jour les compteurs de défauts
                const defectCounts = {};
                Object.values(currentRoll.defects).forEach(defect => {
                    defectCounts[defect.id] = (defectCounts[defect.id] || 0) + 1;
                });
                state.setState('roll.defectCounts', defectCounts, 'user');
                
                // Vérifier la conformité
                commandBus.execute('CHECK_ROLL_CONFORMITY');
            }
            
            return { row, col, defects: currentRoll.defects };
        }
    );
    
    /**
     * Commande : Vérifier la conformité du rouleau
     */
    commandBus.register(
        'CHECK_ROLL_CONFORMITY',
        (payload, state) => {
            const currentRoll = state.getState('production.currentRoll');
            if (!currentRoll) {
                return { conformity: true };
            }
            
            let conformity = true;
            const nonConformityReasons = [];
            
            // Règle 1: Au moins un défaut bloquant
            if (currentRoll.defects) {
                const blockingDefects = Object.values(currentRoll.defects).filter(d => d.severity === 'blocking');
                if (blockingDefects.length > 0) {
                    conformity = false;
                    nonConformityReasons.push(`${blockingDefects.length} défaut(s) bloquant(s)`);
                }
            }
            
            // Règle 2: Plus de 3 cellules avec au moins une épaisseur NOK
            // TODO: Implémenter quand on aura les specs d'épaisseur
            
            // Règle 3: Une cellule a 2 épaisseurs NOK ou plus
            // TODO: Implémenter quand on aura les specs d'épaisseur
            
            // Mettre à jour l'état de conformité
            state.setState('roll.conformity', conformity, 'user');
            state.setState('roll.nonConformityReasons', nonConformityReasons, 'user');
            
            return { conformity, reasons: nonConformityReasons };
        }
    );
    
    /**
     * Commande : Mettre à jour les compteurs de défauts
     */
    commandBus.register(
        'UPDATE_DEFECT_COUNTS',
        (payload, state) => {
            const currentRoll = state.getState('production.currentRoll');
            if (!currentRoll || !currentRoll.defects) {
                state.setState('roll.defectCounts', {}, 'user');
                return { defectCounts: {} };
            }
            
            const defectCounts = {};
            Object.values(currentRoll.defects).forEach(defect => {
                defectCounts[defect.id] = (defectCounts[defect.id] || 0) + 1;
            });
            
            state.setState('roll.defectCounts', defectCounts, 'user');
            
            return { defectCounts };
        }
    );
    
    /**
     * Commande : Marquer un rouleau comme non conforme
     */
    commandBus.register(
        'MARK_ROLL_NON_CONFORM',
        async (payload, state) => {
            const { rollId, cuttingOrderNumber } = payload;
            
            // Récupérer le rouleau
            const rolls = state.getState('production.rolls', []);
            const rollIndex = rolls.findIndex(r => r.id === rollId);
            
            if (rollIndex === -1) {
                throw new Error('Rouleau non trouvé');
            }
            
            const roll = { ...rolls[rollIndex] };
            
            // Générer le nouvel ID pour la découpe
            const newRollId = generateCuttingRollId(cuttingOrderNumber, false);
            
            // Mettre à jour le rouleau
            roll.id = newRollId;
            roll.oldId = rollId;
            roll.conformity = false;
            roll.cuttingOrderNumber = cuttingOrderNumber;
            roll.markedNonConformAt = Date.now();
            
            // Mettre à jour dans l'état
            rolls[rollIndex] = roll;
            state.setState('production.rolls', rolls);
            
            if (state.getState('production.currentRollId') === rollId) {
                state.setState('production.currentRollId', newRollId);
                state.setState('production.currentRoll', roll);
            }
            
            return roll;
        }
    );
    
    /**
     * Commande : Sauvegarder un rouleau
     */
    commandBus.register(
        'SAVE_ROLL',
        async (payload, state) => {
            const { rollId } = payload;
            
            // Récupérer le rouleau
            const rolls = state.getState('production.rolls', []);
            const roll = rolls.find(r => r.id === rollId);
            
            if (!roll) {
                throw new Error('Rouleau non trouvé');
            }
            
            // Préparer les données pour l'API
            const rollData = {
                roll_id: roll.id,
                fabrication_order: roll.ofNumber,
                roll_number: roll.rollNumber,
                target_length: roll.targetLength,
                length: roll.length || 0,
                total_mass: roll.totalMass || 0,
                tube_mass: roll.tubeMass || 0,
                net_mass: roll.netMass || 0,
                grammage: parseFloat(roll.grammage) || 0,
                conformity: roll.conformity,
                thicknesses: roll.thicknesses || [],
                defects: roll.defects || []
            };
            
            // Sauvegarder via l'API
            const response = await window.apiV2.post('/api/rolls/', rollData);
            
            if (!response || !response.id) {
                throw new Error('Erreur lors de la sauvegarde du rouleau');
            }
            
            // Mettre à jour les compteurs
            const okLength = state.getState('counters.woundLengthOk', 0);
            const nokLength = state.getState('counters.woundLengthNok', 0);
            
            if (roll.conformity) {
                state.setState('counters.woundLengthOk', okLength + (roll.length || 0));
            } else {
                state.setState('counters.woundLengthNok', nokLength + (roll.length || 0));
            }
            
            const totalLength = state.getState('counters.woundLengthTotal', 0);
            state.setState('counters.woundLengthTotal', totalLength + (roll.length || 0));
            
            return response;
        }
    );
}

/**
 * Calculer la conformité d'un rouleau
 */
function calculateRollConformity(roll) {
    // Règle 1 : Au moins un défaut bloquant
    if (roll.defects && roll.defects.some(d => d.severity === 'blocking')) {
        return false;
    }
    
    // Règle 2 : Plus de 3 cellules avec au moins une épaisseur NOK
    const cellsWithNok = new Set();
    
    if (roll.thicknesses) {
        roll.thicknesses.forEach(t => {
            if (t.isNok) {
                cellsWithNok.add(`${t.row}-${t.col}`);
            }
        });
    }
    
    if (cellsWithNok.size > 3) {
        return false;
    }
    
    // Règle 3 : Une cellule a 2 épaisseurs NOK ou plus
    const nokCountPerCell = {};
    
    if (roll.thicknesses) {
        roll.thicknesses.forEach(t => {
            if (t.isNok) {
                const key = `${t.row}-${t.col}`;
                nokCountPerCell[key] = (nokCountPerCell[key] || 0) + 1;
            }
        });
    }
    
    if (Object.values(nokCountPerCell).some(count => count >= 2)) {
        return false;
    }
    
    return true;
}
// Exposer globalement
window.registerRollCommands = registerRollCommands;
