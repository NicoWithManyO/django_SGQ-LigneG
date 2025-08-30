/**
 * Service de calculs métier pour les rouleaux
 * Calculs purs sans dépendance au DOM ou Alpine.js
 */

window.rollCalculations = {
    /**
     * Calculer la masse nette
     * @param {number} totalMass - Masse totale en g
     * @param {number} tubeMass - Masse du tube en g
     * @returns {number|null} Masse nette en g
     */
    calculateNetMass(totalMass, tubeMass) {
        const total = parseFloat(totalMass);
        const tube = parseFloat(tubeMass);
        
        if (isNaN(total) || isNaN(tube)) {
            return null;
        }
        
        return total - tube;
    },
    
    /**
     * Calculer le grammage (g/m linéaire)
     * @param {number} netMass - Masse nette en g
     * @param {number} length - Longueur en m
     * @returns {number|null} Grammage en g/m
     */
    calculateGrammage(netMass, length) {
        const net = parseFloat(netMass);
        const len = parseFloat(length);
        
        if (isNaN(net) || isNaN(len) || len <= 0) {
            return null;
        }
        
        // Formule : masse nette / longueur = g/m linéaire
        return net / len;
    },
    
    /**
     * Vérifier le statut du grammage par rapport aux specs
     * @param {number} grammage - Valeur du grammage
     * @param {Object} spec - Spécification avec min/max
     * @returns {string} Status: 'ok', 'alert', 'nok', ''
     */
    checkGrammageStatus(grammage, spec) {
        if (!grammage || !spec) {
            return '';
        }
        
        const value = parseFloat(grammage);
        if (isNaN(value)) {
            return '';
        }
        
        // Vérifier selon les 4 seuils
        if (spec.value_min !== null && value < spec.value_min) {
            return 'nok';
        } else if (spec.value_min_alert !== null && value < spec.value_min_alert) {
            return 'alert';
        } else if (spec.value_max !== null && value > spec.value_max) {
            return 'nok';
        } else if (spec.value_max_alert !== null && value > spec.value_max_alert) {
            return 'alert';
        }
        
        return 'ok';
    },
    
    /**
     * Calculer la moyenne d'un tableau de valeurs
     * @param {Array} values - Tableau de valeurs
     * @returns {number|null} Moyenne ou null si aucune valeur valide
     */
    calculateAverage(values) {
        if (!values || !Array.isArray(values)) {
            return null;
        }
        
        const validValues = values
            .filter(v => v !== null && v !== undefined && v !== '' && !isNaN(v))
            .map(v => parseFloat(v));
            
        if (validValues.length === 0) {
            return null;
        }
        
        const sum = validValues.reduce((acc, val) => acc + val, 0);
        return sum / validValues.length;
    },
    
    /**
     * Générer l'ID d'un rouleau
     * @param {string} ofNumber - Numéro d'OF
     * @param {string} rollNumber - Numéro de rouleau
     * @param {string} status - Status de conformité
     * @param {string} ofDecoupe - OF de découpe (optionnel)
     * @returns {string} ID du rouleau
     */
    generateRollId(ofNumber, rollNumber, status, ofDecoupe = '9999') {
        if (status === 'NON_CONFORME') {
            // Utiliser OF découpe avec date
            const now = new Date();
            const day = now.getDate().toString().padStart(2, '0');
            const month = (now.getMonth() + 1).toString().padStart(2, '0');
            const year = now.getFullYear().toString().slice(-2);
            return `${ofDecoupe}_${day}${month}${year}`;
        } else if (ofNumber && rollNumber && rollNumber.toString().trim() !== '') {
            // Utiliser OF en cours avec numéro de rouleau
            const paddedRollNumber = rollNumber.toString().padStart(3, '0');
            return `${ofNumber}_${paddedRollNumber}`;
        }
        
        return '--';
    },
    
    /**
     * Calculer la masse totale cible pour obtenir un grammage donné
     * @param {number} tubeMass - Masse du tube en g
     * @param {number} length - Longueur en m
     * @param {number} targetGrammage - Grammage cible en g/m
     * @returns {number|null} Masse totale cible en g
     */
    calculateTargetTotalMass(tubeMass, length, targetGrammage = 80) {
        const tube = parseFloat(tubeMass);
        const len = parseFloat(length);
        
        if (isNaN(tube) || isNaN(len) || len <= 0) {
            return null;
        }
        
        // Masse nette = longueur * grammage cible
        const netMass = len * targetGrammage;
        // Masse totale = masse tube + masse nette
        return tube + netMass;
    },
    
    /**
     * Valider les données d'un rouleau pour sauvegarde
     * @param {Object} rollData - Données du rouleau
     * @returns {Object} { isValid: boolean, errors: string[] }
     */
    validateRollData(rollData) {
        const errors = [];
        
        // Vérifier les champs requis
        if (!rollData.shift_id_str) {
            errors.push('ID du poste requis');
        }
        
        if (!rollData.roll_id || rollData.roll_id === '--') {
            errors.push('ID du rouleau invalide');
        }
        
        // Vérifier les masses
        if (rollData.tube_mass !== null && rollData.tube_mass <= 0) {
            errors.push('Masse tube doit être positive');
        }
        
        if (rollData.total_mass !== null && rollData.total_mass <= 0) {
            errors.push('Masse totale doit être positive');
        }
        
        if (rollData.length !== null && rollData.length <= 0) {
            errors.push('Longueur doit être positive');
        }
        
        // Vérifier la cohérence masses
        if (rollData.tube_mass !== null && rollData.total_mass !== null) {
            if (rollData.total_mass <= rollData.tube_mass) {
                errors.push('Masse totale doit être supérieure à la masse tube');
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    },
    
    /**
     * Formater un nombre avec unité
     * @param {number} value - Valeur à formater
     * @param {number} decimals - Nombre de décimales
     * @param {string} unit - Unité
     * @returns {string} Valeur formatée
     */
    formatValue(value, decimals = 0, unit = '') {
        if (value === null || value === undefined || isNaN(value)) {
            return '--';
        }
        
        const formatted = parseFloat(value).toFixed(decimals);
        return unit ? `${formatted} ${unit}` : formatted;
    },
    
    /**
     * Calculer les statistiques QC
     * @param {Object} qcData - Données QC de la session
     * @returns {Object} Statistiques calculées
     */
    calculateQCStats(qcData) {
        const stats = {
            micromaire: {
                left: null,
                right: null,
                average: null
            },
            masseSurfacique: {
                values: [],
                average: null
            }
        };
        
        // Micromaire
        if (qcData.qc_micromaire_g) {
            stats.micromaire.left = this.calculateAverage(qcData.qc_micromaire_g);
        }
        if (qcData.qc_micromaire_d) {
            stats.micromaire.right = this.calculateAverage(qcData.qc_micromaire_d);
        }
        
        // Moyenne globale micromaire
        const micromaireValues = [];
        if (stats.micromaire.left !== null) micromaireValues.push(stats.micromaire.left);
        if (stats.micromaire.right !== null) micromaireValues.push(stats.micromaire.right);
        if (micromaireValues.length > 0) {
            stats.micromaire.average = this.calculateAverage(micromaireValues);
        }
        
        // Masse surfacique
        const masseSurfValues = [];
        ['qc_masse_surfacique_gg', 'qc_masse_surfacique_gc', 
         'qc_masse_surfacique_dc', 'qc_masse_surfacique_dd'].forEach(key => {
            if (qcData[key] && !isNaN(qcData[key])) {
                masseSurfValues.push(parseFloat(qcData[key]));
            }
        });
        
        if (masseSurfValues.length > 0) {
            stats.masseSurfacique.values = masseSurfValues;
            stats.masseSurfacique.average = this.calculateAverage(masseSurfValues);
        }
        
        return stats;
    }
};

// Exposer globalement
window.RollCalculations = window.rollCalculations;