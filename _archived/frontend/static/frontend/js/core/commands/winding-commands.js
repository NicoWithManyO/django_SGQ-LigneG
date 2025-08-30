/**
 * Commandes métier pour la gestion de l'enroulement
 */

function registerWindingCommands(commandBus) {
    
    /**
     * Commande : Mettre à jour le métrage enroulé
     */
    commandBus.register(
        'UPDATE_WOUND_LENGTH',
        async (payload, state) => {
            const { length, source = 'manual' } = payload;
            
            // Valider la longueur
            if (length < 0) {
                throw new Error('La longueur ne peut pas être négative');
            }
            
            // Récupérer l'ancienne valeur
            const oldLength = state.getState('winding.currentLength', 0);
            
            // Mettre à jour la longueur actuelle
            state.setState('winding.currentLength', length);
            
            // Calculer la différence pour mettre à jour les compteurs
            const difference = length - oldLength;
            
            // Mettre à jour le compteur total
            const totalLength = state.getState('winding.totalLength', 0);
            state.setState('winding.totalLength', totalLength + difference);
            
            // Mettre à jour l'historique
            const history = state.getState('winding.history', []);
            history.push({
                timestamp: Date.now(),
                length,
                difference,
                source
            });
            
            // Garder seulement les 100 dernières entrées
            if (history.length > 100) {
                history.splice(0, history.length - 100);
            }
            state.setState('winding.history', history);
            
            return {
                length,
                oldLength,
                difference,
                totalLength: totalLength + difference
            };
        },
        null,
        [
            // Émettre l'événement
            (result) => {
                window.eventBus.emit('winding:length-updated', result);
            }
        ]
    );
    
    /**
     * Commande : Réinitialiser les compteurs d'enroulement
     */
    commandBus.register(
        'RESET_WINDING_COUNTERS',
        async (payload, state) => {
            const { keepHistory = false } = payload;
            
            // Sauvegarder l'état actuel avant reset
            const snapshot = {
                timestamp: Date.now(),
                currentLength: state.getState('winding.currentLength', 0),
                totalLength: state.getState('winding.totalLength', 0),
                okLength: state.getState('winding.okLength', 0),
                nokLength: state.getState('winding.nokLength', 0)
            };
            
            // Réinitialiser les compteurs
            state.setState('winding.currentLength', 0);
            state.setState('winding.totalLength', 0);
            state.setState('winding.okLength', 0);
            state.setState('winding.nokLength', 0);
            
            if (!keepHistory) {
                state.setState('winding.history', []);
            }
            
            // Ajouter le snapshot aux archives
            const archives = state.getState('winding.archives', []);
            archives.push(snapshot);
            state.setState('winding.archives', archives);
            
            return { 
                reset: true, 
                snapshot,
                keepHistory 
            };
        },
        null,
        [
            (result) => {
                window.eventBus.emit('winding:counters-reset', result);
            }
        ]
    );
    
    /**
     * Commande : Mettre à jour les longueurs OK/NOK
     */
    commandBus.register(
        'UPDATE_CONFORMITY_LENGTHS',
        async (payload, state) => {
            const { okLength, nokLength } = payload;
            
            if (okLength !== undefined) {
                state.setState('winding.okLength', Math.max(0, okLength));
            }
            
            if (nokLength !== undefined) {
                state.setState('winding.nokLength', Math.max(0, nokLength));
            }
            
            // Calculer le ratio de conformité
            const totalOk = state.getState('winding.okLength', 0);
            const totalNok = state.getState('winding.nokLength', 0);
            const total = totalOk + totalNok;
            
            const conformityRatio = total > 0 ? (totalOk / total) * 100 : 100;
            state.setState('winding.conformityRatio', conformityRatio);
            
            return {
                okLength: totalOk,
                nokLength: totalNok,
                total,
                conformityRatio
            };
        }
    );
    
    /**
     * Commande : Ajouter une longueur de rouleau
     */
    commandBus.register(
        'ADD_ROLL_LENGTH',
        async (payload, state) => {
            const { rollId, length, isConform } = payload;
            
            if (!rollId || length == null) {
                throw new Error('rollId et length sont requis');
            }
            
            // Mettre à jour les compteurs selon la conformité
            if (isConform) {
                const okLength = state.getState('winding.okLength', 0);
                state.setState('winding.okLength', okLength + length);
            } else {
                const nokLength = state.getState('winding.nokLength', 0);
                state.setState('winding.nokLength', nokLength + length);
            }
            
            // Mettre à jour le total
            const totalLength = state.getState('winding.totalLength', 0);
            state.setState('winding.totalLength', totalLength + length);
            
            // Ajouter à l'historique des rouleaux
            const rollHistory = state.getState('winding.rollHistory', []);
            rollHistory.push({
                rollId,
                length,
                isConform,
                timestamp: Date.now()
            });
            state.setState('winding.rollHistory', rollHistory);
            
            return {
                rollId,
                length,
                isConform,
                newTotal: totalLength + length
            };
        },
        null,
        [
            (result) => {
                window.eventBus.emit('winding:roll-added', result);
            }
        ]
    );
    
    /**
     * Commande : Calculer les statistiques d'enroulement
     */
    commandBus.register(
        'CALCULATE_WINDING_STATS',
        async (payload, state) => {
            const okLength = state.getState('winding.okLength', 0);
            const nokLength = state.getState('winding.nokLength', 0);
            const totalLength = state.getState('winding.totalLength', 0);
            const history = state.getState('winding.history', []);
            
            // Calculer la vitesse moyenne (m/min)
            let averageSpeed = 0;
            if (history.length > 1) {
                const recentHistory = history.slice(-10); // Dernières 10 mesures
                let totalSpeed = 0;
                
                for (let i = 1; i < recentHistory.length; i++) {
                    const timeDiff = (recentHistory[i].timestamp - recentHistory[i-1].timestamp) / 60000; // minutes
                    const lengthDiff = recentHistory[i].difference;
                    
                    if (timeDiff > 0) {
                        totalSpeed += lengthDiff / timeDiff;
                    }
                }
                
                averageSpeed = totalSpeed / (recentHistory.length - 1);
            }
            
            const stats = {
                totalLength,
                okLength,
                nokLength,
                conformityRatio: totalLength > 0 ? (okLength / totalLength) * 100 : 100,
                averageSpeed: Math.round(averageSpeed),
                measurementCount: history.length
            };
            
            state.setState('winding.stats', stats);
            
            return stats;
        }
    );
    
    /**
     * Commande : Définir la longueur cible
     */
    commandBus.register(
        'SET_TARGET_LENGTH',
        async (payload, state) => {
            const { targetLength } = payload;
            
            if (targetLength <= 0) {
                throw new Error('La longueur cible doit être positive');
            }
            
            state.setState('winding.targetLength', targetLength);
            
            // Calculer le pourcentage de progression
            const currentLength = state.getState('winding.currentLength', 0);
            const progress = (currentLength / targetLength) * 100;
            state.setState('winding.progress', Math.min(100, progress));
            
            return {
                targetLength,
                currentLength,
                progress: Math.min(100, progress)
            };
        },
        null,
        [
            (result) => {
                window.eventBus.emit('winding:target-updated', result);
            }
        ]
    );
}

// Exposer globalement
window.registerWindingCommands = registerWindingCommands;