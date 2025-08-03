/**
 * Configuration des règles de validation métier
 */

export function setupRules(validationEngine) {
    
    // === SHIFT VALIDATION RULES ===
    
    // Opérateur - pas requis au chargement initial
    validationEngine.defineRules('shift.operatorId', [
        // La règle required sera ajoutée plus tard si besoin
    ]);
    
    // Date
    validationEngine.defineRules('shift.date', [
        { type: 'date' },
        { type: 'date', max: 'today', message: 'La date ne peut pas être dans le futur' }
    ]);
    
    // Vacation
    validationEngine.defineRules('shift.vacation', [
        { type: 'required', message: 'Sélectionner une vacation' },
        { 
            type: 'pattern', 
            pattern: /^(Matin|ApresMidi|Nuit|Journee)$/,
            message: 'Vacation invalide'
        }
    ]);
    
    // Heures
    validationEngine.defineRules('shift.startTime', [
        { type: 'required', message: 'Heure de début requise' },
        { type: 'time' }
    ]);
    
    validationEngine.defineRules('shift.endTime', [
        { type: 'required', message: 'Heure de fin requise' },
        { type: 'time' }
    ]);
    
    // Longueurs compteur
    validationEngine.defineRules('shift.lengthStart', [
        { 
            type: 'required', 
            message: 'Métrage de début requis si machine démarrée',
            when: (ctx) => ctx.state?.shift?.machineStartedStart === true
        },
        { type: 'numeric' },
        { type: 'range', min: 0, max: 999999 }
    ]);
    
    validationEngine.defineRules('shift.lengthEnd', [
        { 
            type: 'required',
            message: 'Métrage de fin requis si machine démarrée',
            when: (ctx) => ctx.state?.shift?.machineStartedEnd === true
        },
        { type: 'numeric' },
        { type: 'range', min: 0, max: 999999 }
    ]);
    
    // === ROLL VALIDATION RULES ===
    
    // OF Number
    validationEngine.defineRules('roll.ofNumber', [
        { type: 'required', message: 'Numéro OF requis' },
        { type: 'length', min: 1, max: 50 }
    ]);
    
    // Roll Number
    validationEngine.defineRules('roll.rollNumber', [
        { type: 'required', message: 'Numéro de rouleau requis' },
        { type: 'numeric' },
        { type: 'range', min: 1, max: 999 }
    ]);
    
    // Target Length
    validationEngine.defineRules('roll.targetLength', [
        { type: 'required', message: 'Longueur cible requise' },
        { type: 'numeric' },
        { type: 'range', min: 1, max: 1000, message: 'Longueur entre 1 et 1000m' }
    ]);
    
    // Masses
    validationEngine.defineRules('roll.totalMass', [
        { type: 'required', message: 'Masse totale requise' },
        { type: 'numeric' },
        { type: 'range', min: 0.1, max: 9999 }
    ]);
    
    validationEngine.defineRules('roll.tubeMass', [
        { type: 'required', message: 'Masse tube requise' },
        { type: 'numeric' },
        { type: 'range', min: 0.1, max: 999 }
    ]);
    
    // Length mesurée
    validationEngine.defineRules('roll.length', [
        { type: 'required', message: 'Longueur mesurée requise' },
        { type: 'numeric' },
        { type: 'range', min: 0.1, max: 1000 }
    ]);
    
    // === THICKNESS VALIDATION ===
    
    // Enregistrer un validateur personnalisé pour les épaisseurs
    validationEngine.registerValidator('thicknessSpec', (value, context) => {
        const spec = context.spec || {};
        const {
            min = 0,
            minAlert = 0,
            nominal = 5,
            maxAlert = 10,
            max = 10
        } = spec;
        
        const num = parseFloat(value);
        
        if (isNaN(num)) {
            return { valid: false, error: 'Valeur numérique requise' };
        }
        
        // Hors limites = NOK
        if (num < min || num > max) {
            return { 
                valid: false, 
                error: `Épaisseur hors limites (${min}-${max}mm)`,
                severity: 'error'
            };
        }
        
        // En alerte = Warning
        if (num < minAlert || num > maxAlert) {
            return { 
                valid: true,
                warning: `Épaisseur en alerte (optimal: ${minAlert}-${maxAlert}mm)`,
                severity: 'warning'
            };
        }
        
        return { valid: true };
    });
    
    // Règle d'épaisseur
    validationEngine.defineRules('thickness.value', [
        { type: 'required', message: 'Épaisseur requise' },
        { type: 'numeric' },
        { type: 'custom', validator: 'thicknessSpec' }
    ]);
    
    // === LOST TIME VALIDATION ===
    
    validationEngine.defineRules('lostTime.duration', [
        { type: 'required', message: 'Durée requise' },
        { type: 'numeric' },
        { type: 'range', min: 1, max: 480, message: 'Durée entre 1 et 480 minutes' }
    ]);
    
    validationEngine.defineRules('lostTime.reason', [
        { type: 'required', message: 'Sélectionner une raison' }
    ]);
    
    // === CHECKLIST VALIDATION ===
    
    validationEngine.defineRules('checklist.signature', [
        { type: 'required', message: 'Signature requise' },
        { type: 'length', min: 2, max: 50 }
    ]);
    
    // === DEPENDENCIES (Validation croisée) ===
    
    // Dépendance : Machine démarrée nécessite temps de démarrage
    const startupTimeDependency = {
        paths: ['shift.machineStartedStart', 'lostTime.hasStartupTime'],
        message: 'Si la machine n\'est pas démarrée, déclarer le temps de démarrage',
        validate: (data) => {
            const machineStarted = data['shift.machineStartedStart'];
            const hasStartupTime = data['lostTime.hasStartupTime'];
            
            // Si machine démarrée, pas de problème
            if (machineStarted) return true;
            
            // Si machine non démarrée, il faut du temps de démarrage
            return hasStartupTime === true;
        }
    };
    
    // Dépendance : Cohérence des masses
    const massDependency = {
        paths: ['roll.totalMass', 'roll.tubeMass'],
        message: 'La masse totale doit être supérieure à la masse du tube',
        validate: (data) => {
            const totalMass = parseFloat(data['roll.totalMass']) || 0;
            const tubeMass = parseFloat(data['roll.tubeMass']) || 0;
            
            if (totalMass === 0 || tubeMass === 0) return true; // Pas encore rempli
            
            return totalMass > tubeMass;
        }
    };
    
    // Enregistrer les dépendances globalement si nécessaire
    window.validationDependencies = [
        startupTimeDependency,
        massDependency
    ];
    
    console.log('✅ Validation rules configured');
}