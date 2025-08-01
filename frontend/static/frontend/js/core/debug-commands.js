/**
 * Commandes de debug pour vérifier l'état du système V2
 */

// Vérifier les commandes enregistrées
window.checkCommands = function() {
    if (!window.commandBus) {
        console.error('❌ CommandBus non initialisé');
        return;
    }
    
    const commands = window.commandBus.getCommands();
    console.log(`📋 ${commands.length} commandes enregistrées :`);
    commands.forEach(cmd => console.log(`  - ${cmd}`));
    
    // Vérifier les commandes critiques
    const criticalCommands = [
        'CHANGE_OPERATOR',
        'GENERATE_SHIFT_ID',
        'ADD_DEFECT',
        'UNLOCK_FIELD',
        'UPDATE_WOUND_LENGTH'
    ];
    
    console.log('\n🔍 Vérification des commandes critiques :');
    criticalCommands.forEach(cmd => {
        const exists = commands.includes(cmd);
        console.log(`  ${exists ? '✅' : '❌'} ${cmd}`);
    });
};

// Vérifier l'état du StateManager
window.checkState = function(path) {
    if (!window.stateManager) {
        console.error('❌ StateManager non initialisé');
        return;
    }
    
    if (path) {
        const value = window.stateManager.getState(path);
        console.log(`📊 État de '${path}':`, value);
    } else {
        const state = window.stateManager.getState();
        console.log('📊 État complet:', state);
    }
};

// Tester la génération d'ID shift
window.testShiftId = function() {
    if (!window.generateShiftId) {
        console.error('❌ generateShiftId non disponible');
        return;
    }
    
    console.log('🧪 Test de génération d\'ID shift :');
    const result = window.generateShiftId('MartinDUPONT', '2025-01-30', 'Matin');
    console.log('  Résultat:', result);
    console.log('  Attendu: 300125_MartinDupont_Matin');
};

// Forcer l'enregistrement des commandes
window.forceRegisterCommands = function() {
    console.log('🔧 Enregistrement forcé des commandes...');
    
    if (window.registerShiftCommands && window.commandBus) {
        window.registerShiftCommands(window.commandBus);
        console.log('  ✅ Shift commands');
    }
    
    if (window.registerRollCommands && window.commandBus) {
        window.registerRollCommands(window.commandBus);
        console.log('  ✅ Roll commands');
    }
    
    if (window.registerUICommands && window.commandBus) {
        window.registerUICommands(window.commandBus);
        console.log('  ✅ UI commands');
    }
    
    if (window.registerWindingCommands && window.commandBus) {
        window.registerWindingCommands(window.commandBus);
        console.log('  ✅ Winding commands');
    }
    
    window.checkCommands();
};

// Tester une commande
window.testCommand = async function(commandName, payload = {}) {
    if (!window.commandBus) {
        console.error('❌ CommandBus non initialisé');
        return;
    }
    
    try {
        console.log(`🧪 Test de la commande ${commandName} avec:`, payload);
        const result = await window.commandBus.execute(commandName, payload);
        console.log('  ✅ Succès:', result);
        return result;
    } catch (error) {
        console.error('  ❌ Erreur:', error.message);
        throw error;
    }
};

// Afficher un résumé du système
window.systemStatus = function() {
    console.log('🔍 État du système V2\n' + '='.repeat(40));
    
    console.log('\n📦 Modules chargés :');
    console.log(`  ${window.eventBus ? '✅' : '❌'} EventBus`);
    console.log(`  ${window.stateManager ? '✅' : '❌'} StateManager`);
    console.log(`  ${window.commandBus ? '✅' : '❌'} CommandBus`);
    console.log(`  ${window.syncEngine ? '✅' : '❌'} SyncEngine`);
    console.log(`  ${window.validationEngine ? '✅' : '❌'} ValidationEngine`);
    console.log(`  ${window.apiV2 ? '✅' : '❌'} API V2`);
    
    console.log('\n📝 Fonctions de commandes :');
    console.log(`  ${window.registerShiftCommands ? '✅' : '❌'} registerShiftCommands`);
    console.log(`  ${window.registerRollCommands ? '✅' : '❌'} registerRollCommands`);
    console.log(`  ${window.registerUICommands ? '✅' : '❌'} registerUICommands`);
    console.log(`  ${window.registerWindingCommands ? '✅' : '❌'} registerWindingCommands`);
    
    console.log('\n🎯 Composants :');
    console.log(`  ${window.fieldLockManager ? '✅' : '❌'} FieldLockManager`);
    console.log(`  ${window.windingManager ? '✅' : '❌'} WindingManager`);
    console.log(`  ${window.rollGridComponent ? '✅' : '❌'} RollGridComponent`);
    
    if (window.commandBus) {
        const commands = window.commandBus.getCommands();
        console.log(`\n📋 ${commands.length} commandes enregistrées`);
    }
    
    console.log('\n💡 Commandes de debug disponibles :');
    console.log('  - checkCommands() : Liste les commandes');
    console.log('  - checkState(path?) : Affiche l\'état');
    console.log('  - testShiftId() : Teste la génération d\'ID');
    console.log('  - forceRegisterCommands() : Force l\'enregistrement');
    console.log('  - testCommand(name, payload) : Teste une commande');
    console.log('  - systemStatus() : Ce résumé');
};

console.log('🐛 Debug commands loaded. Type systemStatus() to check system state.');