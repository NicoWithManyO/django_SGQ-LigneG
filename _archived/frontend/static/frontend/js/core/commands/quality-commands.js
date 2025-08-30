/**
 * Commandes métier pour la gestion de la qualité
 */

export function registerQualityCommands(commandBus) {
    
    /**
     * Commande : Mettre à jour une cellule du contrôle qualité
     */
    commandBus.register(
        'UPDATE_QC_CELL',
        (payload, state) => {
            const { row, col, status } = payload;
            
            // Récupérer la grille actuelle
            const qcGrid = state.getState('qc.grid', {});
            
            // Mettre à jour la cellule
            const cellKey = `${row}-${col}`;
            qcGrid[cellKey] = {
                row,
                col,
                status, // 'ok', 'nok', 'unchecked'
                updatedAt: Date.now()
            };
            
            state.setState('qc.grid', qcGrid);
            
            // Calculer le statut global
            const totalCells = 12 * 7; // 12 lignes x 7 colonnes
            const checkedCells = Object.values(qcGrid).filter(
                cell => cell.status !== 'unchecked'
            ).length;
            
            let qcStatus = 'pending';
            if (checkedCells === totalCells) {
                qcStatus = 'completed';
            } else if (checkedCells > 0) {
                qcStatus = 'partial';
            }
            
            state.setState('qc.status', qcStatus);
            state.setState('qc.completedCells', checkedCells);
            state.setState('qc.totalCells', totalCells);
            
            if (qcStatus === 'completed') {
                state.setState('qc.completedAt', Date.now());
            }
            
            return { 
                cellKey, 
                status,
                qcStatus,
                progress: `${checkedCells}/${totalCells}`
            };
        },
        // Validateur
        (payload) => {
            const errors = [];
            
            if (payload.row == null || payload.row < 1 || payload.row > 12) {
                errors.push('Ligne invalide (1-12)');
            }
            
            if (payload.col == null || payload.col < 1 || payload.col > 7) {
                errors.push('Colonne invalide (1-7)');
            }
            
            if (!['ok', 'nok', 'unchecked'].includes(payload.status)) {
                errors.push('Statut invalide');
            }
            
            return {
                valid: errors.length === 0,
                errors
            };
        },
        // Effets
        [
            // Émettre l'événement de mise à jour
            (result) => {
                window.eventBus.emit('quality-control-updated', {
                    status: result.qcStatus,
                    progress: result.progress
                });
            }
        ]
    );
    
    /**
     * Commande : Réinitialiser le contrôle qualité
     */
    commandBus.register(
        'RESET_QUALITY_CONTROL',
        (payload, state) => {
            // Réinitialiser la grille
            state.setState('qc.grid', {});
            state.setState('qc.status', 'pending');
            state.setState('qc.completedCells', 0);
            state.setState('qc.totalCells', 84);
            state.setState('qc.completedAt', null);
            
            return { success: true };
        },
        null,
        [
            // Émettre l'événement
            () => {
                window.eventBus.emit('quality-control-updated', {
                    status: 'pending',
                    progress: '0/84'
                });
            }
        ]
    );
    
    /**
     * Commande : Valider le contrôle qualité complet
     */
    commandBus.register(
        'VALIDATE_QUALITY_CONTROL',
        (payload, state) => {
            const qcStatus = state.getState('qc.status');
            const grid = state.getState('qc.grid', {});
            
            // Compter les cellules NOK
            const nokCells = Object.values(grid).filter(
                cell => cell.status === 'nok'
            ).length;
            
            const isComplete = qcStatus === 'completed';
            const hasIssues = nokCells > 0;
            
            return {
                valid: isComplete,
                complete: isComplete,
                nokCount: nokCells,
                hasIssues,
                message: !isComplete ? 
                    'Contrôle qualité non complété' : 
                    hasIssues ? 
                        `${nokCells} points NOK détectés` : 
                        'Contrôle qualité OK'
            };
        }
    );
}