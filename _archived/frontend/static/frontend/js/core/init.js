/**
 * Initialisation du système core
 * 
 * Charge et configure tous les modules du nouveau système
 */

// Configuration globale
window.SGQ_CONFIG = {
    debug: true, // Activer les logs de debug
    api: {
        baseUrl: '/api',
        sessionEndpoint: '/api/session/',
        timeout: 30000
    },
    sync: {
        autoSync: true,
        syncDelay: 300,
        batchSize: 10
    },
    validation: {
        showWarnings: true,
        cacheTimeout: 5000
    }
};

// Activer le mode debug si configuré
window.DEBUG = window.SGQ_CONFIG.debug;

/**
 * Initialiser le système core
 */
async function initializeCore() {
    console.log('🚀 Initializing SGQ Core System...');
    
    try {
        // 1. Vérifier que tous les modules sont chargés
        const requiredModules = [
            'stateManager',
            'commandBus', 
            'validationEngine',
            'eventBus'
        ];
        
        // Vérifier aussi les classes qui doivent être instanciées
        const requiredClasses = ['SyncEngine'];
        
        for (const module of requiredModules) {
            if (!window[module]) {
                throw new Error(`Required module not loaded: ${module}`);
            }
        }
        
        for (const cls of requiredClasses) {
            if (!window[cls]) {
                throw new Error(`Required class not loaded: ${cls}`);
            }
        }
        
        console.log('✅ All core modules loaded');
        
        // 2. Configurer le StateManager AVANT de charger les données
        setupStateManager();
        
        // 3. Charger l'état initial depuis la session APRÈS la config
        await loadInitialState();
        
        // 4. Créer le SyncEngine maintenant que tout est prêt
        if (!window.syncEngine && window.SyncEngine && window.apiV2) {
            window.syncEngine = new window.SyncEngine(window.stateManager, window.apiV2);
            console.log('✅ SyncEngine instance created in init');
        } else {
            console.error('❌ Failed to create SyncEngine:', {
                hasSyncEngine: !!window.syncEngine,
                hasSyncEngineClass: !!window.SyncEngine,
                hasApi: !!window.apiV2
            });
        }
        
        // 5. Configurer le SyncEngine
        setupSyncEngine();
        
        // 6. Enregistrer les commandes métier
        await registerBusinessCommands();
        
        // 7. Configurer les règles de validation
        setupValidationRules();
        
        // 8. Configurer les canaux d'événements
        setupEventChannels();
        
        // 8. Démarrer la synchronisation automatique
        if (window.SGQ_CONFIG.sync.autoSync) {
            startAutoSync();
        }
        
        // 9. Charger le profil actuel APRÈS que les commandes soient enregistrées
        await loadCurrentProfile();
        
        console.log('✅ SGQ Core System initialized successfully');
        
        // Émettre un événement de système prêt
        window.eventBus.emit('system:ready', {
            timestamp: Date.now(),
            modules: requiredModules
        });
        
    } catch (error) {
        console.error('❌ Core initialization failed:', error);
        
        // Émettre un événement d'erreur système
        if (window.eventBus) {
            window.eventBus.emit('system:error', {
                error: error.message,
                phase: 'initialization'
            });
        }
        
        throw error;
    }
}

/**
 * Configurer le StateManager
 */
function setupStateManager() {
    // Initialiser SEULEMENT si la structure n'existe pas déjà
    const existingProduction = window.stateManager.getState('production');
    if (!existingProduction) {
        window.stateManager.setState('production', {
            currentRoll: {
                thicknesses: {}
            },
            currentRollNumber: null,
            currentRollId: null,
            nextTubeWeight: null,
            rolls: []
        }, 'system');
    } else {
        // S'assurer que currentRoll existe
        if (!existingProduction.currentRoll) {
            existingProduction.currentRoll = { thicknesses: {} };
            window.stateManager.setState('production', existingProduction, 'system');
        }
    }
    
    // Middleware de validation
    window.stateManager.use(({ path, value, source }) => {
        // Ne valider que les changements utilisateur
        if (source !== 'user') return value;
        
        // Valider la valeur
        const validation = window.validationEngine.validate(path, value, {
            state: window.stateManager.getState()
        });
        
        if (!validation.valid) {
            console.warn(`Validation failed for ${path}:`, validation.errors);
            
            // Émettre un événement de validation
            window.eventBus.emit('validation:failed', {
                path,
                value,
                errors: validation.errors
            });
            
            // On pourrait bloquer la valeur ici si nécessaire
            // throw new Error(validation.errors[0].message);
        }
        
        if (validation.warnings.length > 0 && window.SGQ_CONFIG.validation.showWarnings) {
            console.warn(`Validation warnings for ${path}:`, validation.warnings);
            
            window.eventBus.emit('validation:warning', {
                path,
                value,
                warnings: validation.warnings
            });
        }
        
        return value;
    });
    
    // Middleware de transformation
    window.stateManager.use(({ path, value }) => {
        // Transformer les valeurs numériques
        if (path.includes('length') || path.includes('mass') || path.includes('thickness')) {
            if (typeof value === 'string' && value !== '') {
                return parseFloat(value.replace(',', '.')) || 0;
            }
        }
        
        return value;
    });
}

/**
 * Configurer le SyncEngine
 */
function setupSyncEngine() {
    // Intercepteur pour logger les synchronisations
    window.stateManager.subscribe('sync.error', (error) => {
        console.error('Sync error:', error);
        
        // Afficher une notification à l'utilisateur
        window.eventBus.emit('notification:error', {
            message: 'Erreur de synchronisation avec le serveur',
            details: error.error
        });
    });
    
    // Surveiller l'état de synchronisation
    setInterval(() => {
        if (window.syncEngine) {
            const syncState = window.syncEngine.getSyncState();
            
            if (syncState.failed > 0) {
                window.eventBus.emit('sync:status', {
                    ...syncState,
                    hasErrors: true
                });
            }
        }
    }, 5000);
}

/**
 * Charger le profil actuel depuis la BDD
 */
async function loadCurrentProfile() {
    try {
        // D'abord vérifier si on a un profile_id en session
        const sessionProfileId = window.stateManager.getState('profile.id');
        if (sessionProfileId) {
            console.log('Profile ID trouvé en session:', sessionProfileId);
            // Charger les données complètes du profil
            await window.commandBus.execute('CHANGE_PROFILE', { 
                profileId: sessionProfileId 
            });
            return;
        }
        
        // Sinon, charger depuis la BDD
        const response = await window.apiV2.get('/production/api/current-profile/');
        if (response && response.profile_id) {
            // Charger les données complètes du profil
            await window.commandBus.execute('CHANGE_PROFILE', { 
                profileId: response.profile_id 
            });
            console.log('✅ Profil actuel chargé depuis BDD:', response.profile_name);
        }
    } catch (error) {
        console.warn('Pas de profil actuel en BDD:', error);
    }
}

/**
 * Enregistrer les commandes métier
 */
async function registerBusinessCommands() {
    console.log('Registering business commands...');
    
    // Ne PAS essayer d'importer index.js qui utilise ES6 modules
    // Les commandes sont enregistrées directement après
    
    // Enregistrer les commandes shift
    if (window.registerShiftCommands) {
        window.registerShiftCommands(window.commandBus);
        console.log('✅ Shift commands registered');
    }
    
    // Enregistrer les commandes du rouleau
    if (window.registerRollCommands) {
        window.registerRollCommands(window.commandBus);
        console.log('✅ Roll commands registered');
    }
    
    // Enregistrer les commandes UI
    if (window.registerUICommands) {
        window.registerUICommands(window.commandBus);
        console.log('✅ UI commands registered');
    }
    
    // Enregistrer les commandes profil
    if (window.registerProfileCommands) {
        window.registerProfileCommands(window.commandBus);
        console.log('✅ Profile commands registered');
    }
    
    // Enregistrer les commandes d'enroulement
    if (window.registerWindingCommands) {
        window.registerWindingCommands(window.commandBus);
        console.log('✅ Winding commands registered');
    }
    
    // Définir les règles de validation pour les défauts
    if (window.validationEngine) {
        // Règles pour ADD_DEFECT
        window.validationEngine.defineRules('defect.row', [
            { type: 'required', message: 'Ligne requise' },
            { type: 'numeric' },
            { type: 'range', min: 0, max: 9 }
        ]);
        
        window.validationEngine.defineRules('defect.col', [
            { type: 'required', message: 'Colonne requise' },
            { type: 'numeric' },
            { type: 'range', min: 0, max: 19 }
        ]);
        
        window.validationEngine.defineRules('defect.id', [
            { type: 'required', message: 'ID du défaut requis' },
            { type: 'numeric' }
        ]);
        
        window.validationEngine.defineRules('defect.name', [
            { type: 'required', message: 'Nom du défaut requis' },
            { type: 'length', min: 1, max: 100 }
        ]);
        
        window.validationEngine.defineRules('defect.severity', [
            { type: 'required', message: 'Sévérité requise' },
            { 
                type: 'pattern', 
                pattern: /^(normal|major|blocking)$/,
                message: 'Sévérité invalide'
            }
        ]);
        
        console.log('✅ Defect validation rules registered');
    }
}

/**
 * Enregistrer les commandes de base manuellement
 */
function registerBasicCommands() {
    // Commande CHANGE_OPERATOR basique
    window.commandBus.register(
        'CHANGE_OPERATOR',
        async (payload, state) => {
            const { operatorId } = payload;
            state.setState('shift.operatorId', operatorId);
            
            // Générer l'ID si possible
            const date = state.getState('shift.date');
            const vacation = state.getState('shift.vacation');
            
            if (operatorId && date && vacation && window.operators) {
                const operator = window.operators.find(op => op.id == operatorId);
                if (operator) {
                    const dateObj = new Date(date);
                    const dateStr = dateObj.toLocaleDateString('fr-FR').replace(/\//g, '');
                    const operatorName = `${operator.first_name}${operator.last_name.toUpperCase()}`;
                    const shiftId = `${dateStr}_${operatorName}_${vacation}`;
                    
                    state.setState('shift.id', shiftId);
                    state.setState('shift.idStatus', 'valid');
                }
            }
            
            return { operatorId };
        }
    );
    
    // Commande CHANGE_SHIFT_DATE
    window.commandBus.register(
        'CHANGE_SHIFT_DATE',
        async (payload, state) => {
            const { date } = payload;
            state.setState('shift.date', date);
            
            // Recalculer l'ID
            await window.commandBus.execute('GENERATE_SHIFT_ID');
            
            return { date };
        }
    );
    
    // Commande CHANGE_VACATION
    window.commandBus.register(
        'CHANGE_VACATION',
        async (payload, state) => {
            const { vacation } = payload;
            state.setState('shift.vacation', vacation);
            
            // Heures par défaut
            const defaultHours = {
                'Matin': { start: '04:00', end: '12:00' },
                'ApresMidi': { start: '12:00', end: '20:00' },
                'Nuit': { start: '20:00', end: '04:00' },
                'Journee': { start: '07:30', end: '15:30' }
            };
            
            if (defaultHours[vacation]) {
                state.setState('shift.startTime', defaultHours[vacation].start);
                state.setState('shift.endTime', defaultHours[vacation].end);
            }
            
            // Recalculer l'ID
            await window.commandBus.execute('GENERATE_SHIFT_ID');
            
            return { vacation };
        }
    );
    
    // Commande GENERATE_SHIFT_ID
    window.commandBus.register(
        'GENERATE_SHIFT_ID',
        (payload, state) => {
            const operatorId = state.getState('shift.operatorId');
            const date = state.getState('shift.date');
            const vacation = state.getState('shift.vacation');
            
            if (operatorId && date && vacation && window.operators) {
                const operator = window.operators.find(op => op.id == operatorId);
                if (operator) {
                    const dateObj = new Date(date);
                    const day = String(dateObj.getDate()).padStart(2, '0');
                    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                    const year = String(dateObj.getFullYear()).slice(-2);
                    const dateStr = `${day}${month}${year}`;
                    const operatorName = `${operator.first_name}${operator.last_name.toUpperCase()}`;
                    const shiftId = `${dateStr}_${operatorName}_${vacation}`;
                    
                    state.setState('shift.id', shiftId);
                    state.setState('shift.idStatus', 'valid');
                    
                    return { shiftId };
                }
            }
            
            state.setState('shift.id', null);
            state.setState('shift.idStatus', 'empty');
            return { shiftId: null };
        }
    );
    
    console.log('✅ Basic commands registered');
}

/**
 * Configurer les règles de validation
 */
function setupValidationRules() {
    // Charger le module de règles
    import('./validation/rules.js').then(rulesModule => {
        if (rulesModule && rulesModule.setupRules) {
            rulesModule.setupRules(window.validationEngine);
            console.log('✅ Validation rules configured');
        }
    }).catch(error => {
        console.warn('Could not load validation rules:', error);
    });
}

/**
 * Configurer les canaux d'événements
 */
function setupEventChannels() {
    // Canal pour les notifications
    window.notificationChannel = window.eventBus.channel('notification');
    
    // Canal pour les mises à jour de production
    window.productionChannel = window.eventBus.channel('production');
    
    // Canal pour les validations
    window.validationChannel = window.eventBus.channel('validation');
    
    // Canal système
    window.systemChannel = window.eventBus.channel('system');
}

/**
 * Charger l'état initial depuis la session
 */
async function loadInitialState() {
    console.log('Loading initial state from session...');
    
    // Si pas de données de session dans le DOM, charger depuis l'API
    if (!window.sessionData) {
        try {
            const response = await fetch('/api/session/');
            if (response.ok) {
                window.sessionData = await response.json();
                console.log('Session data loaded from API:', window.sessionData);
            } else {
                console.warn('Failed to load session data from API');
                window.sessionData = {};
            }
        } catch (error) {
            console.error('Error loading session data:', error);
            window.sessionData = {};
        }
    }
    
    // Mapper les données de session vers l'état - UNIQUEMENT V2
    const mappings = {
        // V2 data only - with v2_ prefix
        'v2_shift_operator_id': 'shift.operatorId',
        'v2_shift_date': 'shift.date',
        'v2_shift_vacation': 'shift.vacation',
        'v2_shift_start_time': 'shift.startTime',
        'v2_shift_end_time': 'shift.endTime',
        'v2_shift_comment': 'shift.comment',
        'v2_shift_id': 'shift.id',
        
        // Machine started and lengths
        'shift_form_machine_started_start': 'shift.machineStartedStart',
        'shift_form_machine_started_end': 'shift.machineStartedEnd',
        'shift_form_length_start': 'shift.lengthStart',
        'shift_form_length_end': 'shift.lengthEnd',
        
        // Sticky bar data
        'current_roll_number': 'production.currentRollNumber',
        'current_roll_id': 'production.currentRollId',
        'current_roll_tube_mass': 'production.currentRoll.tubeMass',
        'current_roll_length': 'production.currentRoll.length',
        'current_roll_total_mass': 'production.currentRoll.totalMass',
        'current_roll_thicknesses': 'production.currentRoll.thicknesses',
        'next_tube_weight': 'production.nextTubeWeight',
        
        // OF data
        'of_en_cours': 'of.enCours',
        'target_length': 'of.targetLength',
        
        // Profile data
        'profile_id': 'profile.id',
        
        // V2 production data
        'v2_production_profile_id': 'production.currentProfileId',
        'v2_production_of_number': 'production.currentOfNumber',
        'v2_production_target_length': 'production.currentTargetLength',
        
        // V2 counters
        'v2_counters_ok': 'counters.woundLengthOk',
        'v2_counters_nok': 'counters.woundLengthNok',
        'v2_counters_total': 'counters.woundLengthTotal',
        
        // V2 rolls
        'v2_rolls': 'production.rolls',
        
        // V2 roll measurements and defects
        'v2_roll_measurements': 'roll.measurements',
        'v2_roll_defects': 'roll.defects',
        'v2_roll_conformity': 'roll.conformity'
    };
    
    // Initialiser production.currentRoll avec toutes les propriétés nécessaires
    let production = window.stateManager.getState('production');
    if (!production) {
        production = {};
        window.stateManager.setState('production', production, 'system');
    }
    
    if (!production.currentRoll) {
        production.currentRoll = {
            thicknesses: {},
            tubeMass: null,
            length: null,
            totalMass: null
        };
        window.stateManager.setState('production', production, 'system');
    }
    
    
    // Charger les données dans le state
    for (const [sessionKey, statePath] of Object.entries(mappings)) {
        if (window.sessionData.hasOwnProperty(sessionKey)) {
            // Silently load from session
            
            // Pour les chemins imbriqués dans currentRoll, traiter spécialement
            if (statePath.startsWith('production.currentRoll.')) {
                // S'assurer que production.currentRoll existe
                let currentRoll = window.stateManager.getState('production.currentRoll');
                if (!currentRoll) {
                    currentRoll = {};
                }
                
                // Extraire la propriété (ex: 'thicknesses' de 'production.currentRoll.thicknesses')
                const property = statePath.split('.').pop();
                currentRoll[property] = window.sessionData[sessionKey];
                
                window.stateManager.setState('production.currentRoll', currentRoll, 'system');
            } else {
                window.stateManager.setState(
                    statePath, 
                    window.sessionData[sessionKey],
                    'system'
                );
            }
        }
    }
    
    console.log('✅ Initial state loaded');
    
    // Restaurer l'état UI après un délai pour s'assurer que tous les composants sont prêts
    setTimeout(() => {
        if (window.commandBus) {
            window.commandBus.execute('RESTORE_UI_STATE', {});
        }
    }, 500);
    
    // Émettre l'événement que l'état est chargé
    if (window.eventBus) {
        window.eventBus.emit('state:loaded');
    }
}

/**
 * Démarrer la synchronisation automatique
 */
function startAutoSync() {
    // NE PAS synchroniser automatiquement - on le fera seulement sur blur
    console.log('✅ Auto-sync disabled - will sync on blur only');
}

/**
 * Fonction utilitaire pour attendre que le DOM soit prêt
 */
function domReady(callback) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', callback);
    } else {
        callback();
    }
}

// Exposer la fonction d'initialisation
window.initializeCore = initializeCore;

// Exposer une fonction pour synchroniser manuellement
window.syncField = function(path, value) {
    if (window.syncEngine) {
        window.syncEngine.sync(path, value, 'normal', true); // immediate = true
    }
};

// Auto-initialisation désactivée - le template appelle initializeCore()
// Pour activer l'auto-init, définir window.SGQ_MANUAL_INIT = false avant de charger ce script