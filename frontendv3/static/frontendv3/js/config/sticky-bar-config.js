/**
 * Configuration pour le composant sticky-bar
 * Extraction des constantes et configuration
 */

window.stickyBarConfig = {
    // Configuration de l'horloge
    clock: {
        updateInterval: 1000, // ms
        locale: 'fr-FR',
        options: {
            weekday: 'short',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }
    },
    
    // Configuration des IDs
    rollId: {
        ofDecoupe: '9999',
        padLength: 3,
        dateFormat: 'DDMMYY' // Format de date pour rouleau non conforme
    },
    
    // Configuration des validations
    validation: {
        minTubeMass: 0,
        minTotalMass: 0,
        minLength: 0,
        defaultTargetGrammage: 80 // g/m
    },
    
    // Configuration des masses tube
    tubeMass: {
        baseValue: 900, // g
        variation: 50, // ±50g
        generateRandom: () => {
            const variation = Math.floor(Math.random() * 101) - 50;
            return window.stickyBarConfig.tubeMass.baseValue + variation;
        }
    },
    
    // Timeouts et délais
    timeouts: {
        saveNotification: 3000, // ms
        pageReload: 500, // ms
        checklistFill: 100 // ms
    },
    
    // URLs API
    api: {
        checkRollId: '/production/api/rolls/check-id/',
        nextRollNumber: '/production/api/rolls/next-number/',
        saveRoll: '/production/api/rolls/',
        lastShift: '/production/api/shifts/last/'
    },
    
    // Messages
    messages: {
        noOf: 'Aucun OF sélectionné',
        nextNumber: 'Prochain numéro : ',
        rollSaved: 'Rouleau {rollId} sauvegardé',
        savingRoll: 'Sauvegarde du rouleau...',
        savingAll: 'Sauvegarde en cours...',
        saveSuccess: 'Données sauvegardées avec succès',
        saveError: 'Erreur lors de la sauvegarde',
        fetchError: 'Erreur lors de la récupération du numéro',
        confirmClear: 'Êtes-vous sûr de vouloir vider toutes les données (sauf les OF) ?',
        magicWand: '🎩 Baguette magique : Tout est rempli !',
        exportPending: 'Export en préparation...'
    },
    
    // Validation messages
    validationMessages: {
        operatorRequired: 'Opérateur requis',
        dateRequired: 'Date requise',
        vacationRequired: 'Vacation requise',
        grammageRequired: 'Grammage requis (masse + longueur)',
        thicknessRequired: 'Toutes les épaisseurs requises',
        invalidRollId: 'ID du rouleau invalide',
        shiftIdRequired: 'ID du poste requis',
        positiveTubeMass: 'Masse tube doit être positive',
        positiveTotalMass: 'Masse totale doit être positive',
        positiveLength: 'Longueur doit être positive',
        totalMassGreaterThanTube: 'Masse totale doit être supérieure à la masse tube'
    }
};

// Export
window.StickyBarConfig = window.stickyBarConfig;