/**
 * Service de calcul de conformité pour les rouleaux
 * Extrait depuis roll-grid.js pour centraliser la logique métier
 */

window.conformityService = {
    /**
     * Calculer le statut de conformité d'un rouleau
     * @param {Object} data - Données nécessaires au calcul
     * @param {Object} data.rattrapages - Map des rattrapages {cellKey: nokValue}
     * @param {Object} data.thicknessValues - Map des épaisseurs {cellKey: value}
     * @param {Object} data.thicknessSpec - Spécification d'épaisseur avec min/max
     * @param {Object} data.defects - Map des défauts {cellKey: [defectNames]}
     * @param {Array} data.defectTypes - Types de défauts avec severity et threshold
     * @param {number} data.nokLimit - Limite de NOK (peut être null)
     * @returns {string} 'CONFORME' ou 'NON_CONFORME'
     */
    calculateConformityStatus(data) {
        debug('=== CALCULATING CONFORMITY STATUS ===');
        
        // 1. Vérifier s'il y a des NOK non rattrapés
        const hasUnrecovered = this.hasUnrecoveredNOK(
            data.rattrapages, 
            data.thicknessValues, 
            data.thicknessSpec
        );
        debug(`Has unrecovered NOK: ${hasUnrecovered}`);
        if (hasUnrecovered) {
            return 'NON_CONFORME';
        }
        
        // 2. Vérifier les défauts bloquants
        const blockingDefects = this.checkBlockingDefects(
            data.defects, 
            data.defectTypes
        );
        debug(`Has blocking defects: ${blockingDefects.hasBlocking}`);
        if (blockingDefects.hasBlocking) {
            debug(`Blocking defect found: ${blockingDefects.defectName}`);
            return 'NON_CONFORME';
        }
        
        // 3. Vérifier les défauts avec seuil
        const thresholdDefects = this.checkThresholdDefects(
            data.defects, 
            data.defectTypes
        );
        debug(`Threshold defects exceeded: ${thresholdDefects.exceeded}`);
        if (thresholdDefects.exceeded) {
            debug(`Threshold exceeded for: ${thresholdDefects.defectName} (${thresholdDefects.count}/${thresholdDefects.threshold})`);
            return 'NON_CONFORME';
        }
        
        // 4. Vérifier la limite de NOK uniquement si elle est définie et > 0
        if (data.nokLimit !== null && data.nokLimit !== undefined && data.nokLimit > 0) {
            const nokCount = this.countNonConformingThicknesses(data.rattrapages);
            debug(`NOK count: ${nokCount}, limit: ${data.nokLimit}`);
            if (nokCount >= data.nokLimit) {
                debug('NOK count exceeds limit -> NON CONFORME');
                return 'NON_CONFORME';
            }
        }
        
        // Si aucun critère de non-conformité n'est rempli
        debug('All criteria passed -> CONFORME');
        return 'CONFORME';
    },
    
    /**
     * Vérifier s'il y a des épaisseurs NOK non rattrapées
     */
    hasUnrecoveredNOK(rattrapages, thicknessValues, thicknessSpec) {
        debug('Checking unrecovered NOK. Rattrapages:', rattrapages);
        debug('ThicknessValues:', thicknessValues);
        debug('Thickness spec:', thicknessSpec);
        
        if (!thicknessSpec) return false;
        
        const min = thicknessSpec.value_min;
        const max = thicknessSpec.value_max;
        
        // Les valeurs NOK sont dans rattrapages
        // Les rattrapages (corrections) sont dans thicknessValues
        for (const [key, nokValue] of Object.entries(rattrapages)) {
            if (nokValue) {
                // On a une valeur NOK d'origine
                // Vérifier si elle a été rattrapée
                const correctedValue = thicknessValues[key];
                debug(`Cell ${key}: NOK=${nokValue}, Corrected=${correctedValue}`);
                
                if (!correctedValue) {
                    // Pas de correction saisie
                    debug(`Cell ${key}: No correction entered for NOK value`);
                    return true;
                }
                
                // Vérifier si la correction est dans les limites
                const correctedFloat = parseFloat(correctedValue);
                if (isNaN(correctedFloat)) {
                    debug(`Cell ${key}: Invalid correction value`);
                    return true;
                }
                
                if (correctedFloat < min || correctedFloat > max) {
                    // La correction est elle-même NOK
                    debug(`Cell ${key}: Correction ${correctedFloat} is out of bounds [${min}, ${max}]`);
                    return true;
                }
            }
        }
        
        debug('All NOK values have been properly corrected');
        return false;
    },
    
    /**
     * Vérifier les défauts bloquants
     */
    checkBlockingDefects(defects, defectTypes) {
        if (!defectTypes) return { hasBlocking: false };
        
        // Parcourir tous les défauts enregistrés
        for (const cellDefects of Object.values(defects)) {
            for (const defectName of cellDefects) {
                // Trouver le type de défaut correspondant
                const defectType = defectTypes.find(d => d.name === defectName);
                if (defectType && defectType.severity === 'blocking') {
                    return { hasBlocking: true, defectName: defectName };
                }
            }
        }
        
        return { hasBlocking: false };
    },
    
    /**
     * Vérifier les défauts avec seuil
     */
    checkThresholdDefects(defects, defectTypes) {
        if (!defectTypes) return { exceeded: false };
        
        // Compter les occurrences de chaque type de défaut
        const defectCounts = {};
        for (const cellDefects of Object.values(defects)) {
            for (const defectName of cellDefects) {
                defectCounts[defectName] = (defectCounts[defectName] || 0) + 1;
            }
        }
        
        // Vérifier les seuils
        for (const [defectName, count] of Object.entries(defectCounts)) {
            const defectType = defectTypes.find(d => d.name === defectName);
            if (defectType && defectType.severity === 'threshold' && 
                defectType.threshold !== undefined && defectType.threshold !== null) {
                if (count >= defectType.threshold) {
                    return { 
                        exceeded: true, 
                        defectName: defectName,
                        count: count,
                        threshold: defectType.threshold
                    };
                }
            }
        }
        
        return { exceeded: false };
    },
    
    /**
     * Compter le nombre total d'épaisseurs NOK
     */
    countNonConformingThicknesses(rattrapages) {
        // Compter simplement toutes les valeurs dans rattrapages
        // Car toute valeur dans rattrapages est une NOK d'origine
        return Object.keys(rattrapages).length;
    },
    
    /**
     * Obtenir la classe CSS pour un statut d'épaisseur
     * @param {number} value - Valeur d'épaisseur
     * @param {Object} spec - Spécification avec limites
     * @returns {string} Classe CSS
     */
    getThicknessStatusClass(value, spec) {
        if (!spec || value === null || value === undefined || value === '') {
            return '';
        }
        
        const val = parseFloat(value);
        if (isNaN(val)) return '';
        
        // Vérifier selon les 4 seuils
        if (spec.value_min !== null && val < spec.value_min) {
            return 'nok';
        } else if (spec.value_min_alert !== null && val < spec.value_min_alert) {
            return 'alert';
        } else if (spec.value_max !== null && val > spec.value_max) {
            return 'nok';
        } else if (spec.value_max_alert !== null && val > spec.value_max_alert) {
            return 'alert';
        }
        
        return 'ok';
    },
    
    /**
     * Valider si toutes les épaisseurs sont remplies
     * @param {Object} thicknessValues - Map des épaisseurs
     * @param {number} totalCells - Nombre total de cellules attendues
     * @returns {boolean}
     */
    areAllThicknessesFilled(thicknessValues, totalCells) {
        const filledCount = Object.values(thicknessValues)
            .filter(v => v !== null && v !== undefined && v !== '').length;
        return filledCount === totalCells;
    },
    
    /**
     * Compter les défauts par type
     * @param {Object} defects - Map des défauts
     * @returns {Object} Comptage par type de défaut
     */
    countDefectsByType(defects) {
        const counts = {};
        
        for (const cellDefects of Object.values(defects)) {
            for (const defectName of cellDefects) {
                counts[defectName] = (counts[defectName] || 0) + 1;
            }
        }
        
        return counts;
    },
    
    /**
     * Obtenir un résumé de la conformité
     * @param {Object} data - Mêmes données que calculateConformityStatus
     * @returns {Object} Résumé détaillé
     */
    getConformitySummary(data) {
        const status = this.calculateConformityStatus(data);
        const nokCount = this.countNonConformingThicknesses(data.rattrapages);
        const defectCounts = this.countDefectsByType(data.defects);
        const hasUnrecovered = this.hasUnrecoveredNOK(
            data.rattrapages, 
            data.thicknessValues, 
            data.thicknessSpec
        );
        const blockingDefects = this.checkBlockingDefects(data.defects, data.defectTypes);
        const thresholdDefects = this.checkThresholdDefects(data.defects, data.defectTypes);
        
        return {
            status,
            nokCount,
            nokLimit: data.nokLimit,
            hasUnrecoveredNOK: hasUnrecovered,
            hasBlockingDefects: blockingDefects.hasBlocking,
            blockingDefectName: blockingDefects.defectName,
            hasThresholdExceeded: thresholdDefects.exceeded,
            thresholdDefectName: thresholdDefects.defectName,
            thresholdCount: thresholdDefects.count,
            thresholdLimit: thresholdDefects.threshold,
            defectCounts,
            totalDefects: Object.values(defectCounts).reduce((sum, count) => sum + count, 0)
        };
    }
};

// Export
window.ConformityService = window.conformityService;