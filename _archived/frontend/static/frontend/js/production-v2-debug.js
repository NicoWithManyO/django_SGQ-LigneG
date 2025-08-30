/**
 * Fonctions de debug pour Production V2
 */

// ===== FONCTIONS DE DEBUG =====
window.logDebug = function(message, type = 'info') {
    const log = document.getElementById('debug-log');
    if (!log) return;
    
    const time = new Date().toLocaleTimeString();
    const colors = {
        info: '#90caf9',
        success: '#81c784',
        error: '#ef5350',
        warning: '#ffb74d'
    };
    
    const entry = document.createElement('div');
    entry.style.color = colors[type] || colors.info;
    entry.innerHTML = `[${time}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
    
    // Log aussi dans la console
    console.log(`[${type.toUpperCase()}] ${message}`);
};

window.clearDebug = function() {
    const log = document.getElementById('debug-log');
    if (log) {
        log.innerHTML = '<div style="color: var(--v2-success-light);">Debug console cleared...</div>';
    }
};

window.toggleDebugPanel = function() {
    const panel = document.getElementById('debug-panel');
    if (!panel) return;
    
    if (panel.style.height === '40px') {
        panel.style.height = 'auto';
    } else {
        panel.style.height = '40px';
    }
};

window.toggleDebugConsole = function() {
    const panel = document.getElementById('debug-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
};

// ===== TESTS API =====
window.testSession = async function() {
    logDebug('Test Session API...', 'info');
    
    try {
        const response = await fetch('/api/session/', {
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            logDebug('✅ Session API: OK', 'success');
            
            // Test des données principales
            const tests = [
                { key: 'operator_id', label: 'Opérateur' },
                { key: 'shift_id', label: 'ID Poste' },
                { key: 'shift_form_shift_date', label: 'Date poste' },
                { key: 'shift_form_vacation', label: 'Vacation' },
                { key: 'of_en_cours', label: 'OF en cours' },
                { key: 'target_length', label: 'Longueur cible' },
                { key: 'profile_id', label: 'Profil' }
            ];
            
            tests.forEach(test => {
                if (data[test.key]) {
                    logDebug(`✅ ${test.label}: ${data[test.key]}`, 'success');
                } else {
                    logDebug(`⚠️ ${test.label}: non défini`, 'warning');
                }
            });
            
            // Test des données rouleau
            if (data.roll_measurements && Object.keys(data.roll_measurements).length > 0) {
                logDebug(`✅ Mesures d'épaisseur: ${Object.keys(data.roll_measurements).length} enregistrées`, 'success');
            } else {
                logDebug('⚠️ Mesures d\'épaisseur: aucune', 'warning');
            }
            
            if (data.roll_defects && Object.keys(data.roll_defects).length > 0) {
                logDebug(`✅ Défauts: ${Object.keys(data.roll_defects).length} positions avec défauts`, 'success');
            } else {
                logDebug('⚠️ Défauts: aucun', 'warning');
            }
            
            // Afficher un résumé complet
            logDebug('--- Résumé complet ---', 'info');
            console.log('Session complète:', data);
        } else {
            logDebug(`❌ Session API: ${response.status}`, 'error');
        }
    } catch (error) {
        logDebug('❌ Erreur réseau: ' + error.message, 'error');
    }
};

window.testConnection = async function() {
    logDebug('Test de connexion et synchronisation...', 'info');
    
    // Test 1: Vérifier les modules core
    logDebug('--- Test des modules Core V2 ---', 'info');
    const modules = [
        { name: 'StateManager', obj: window.stateManager },
        { name: 'CommandBus', obj: window.commandBus },
        { name: 'SyncEngine', obj: window.syncEngine },
        { name: 'EventBus', obj: window.eventBus },
        { name: 'API V2', obj: window.api }
    ];
    
    let coreOk = true;
    modules.forEach(module => {
        if (module.obj) {
            logDebug(`✅ ${module.name} chargé`, 'success');
        } else {
            logDebug(`❌ ${module.name} manquant`, 'error');
            coreOk = false;
        }
    });
    
    // Test 2: État de synchronisation
    if (window.syncEngine) {
        logDebug('--- État de synchronisation ---', 'info');
        const syncState = window.syncEngine.getSyncState();
        
        if (syncState.pending > 0) {
            logDebug(`⏳ ${syncState.pending} éléments en attente de sync`, 'warning');
        } else {
            logDebug('✅ Aucune sync en attente', 'success');
        }
        
        if (syncState.failed > 0) {
            logDebug(`❌ ${syncState.failed} syncs échouées`, 'error');
            if (syncState.lastError) {
                logDebug(`  → Dernière erreur: ${syncState.lastError}`, 'error');
            }
        }
        
        if (syncState.lastSyncTime) {
            const ago = Math.round((Date.now() - syncState.lastSyncTime) / 1000);
            logDebug(`⏰ Dernière sync il y a ${ago}s`, 'info');
        }
    }
    
    // Test 3: Endpoints API
    logDebug('--- Test des endpoints API ---', 'info');
    const endpoints = [
        { url: '/api/session/', name: 'Session', critical: true },
        { url: '/api/operators/', name: 'Opérateurs', critical: true },
        { url: '/api/fabrication-orders/', name: 'Ordres de Fabrication', critical: true },
        { url: '/api/profiles/', name: 'Profils', critical: true },
        { url: '/api/defect-types/', name: 'Types défauts', critical: true },
        { url: '/api/shifts/', name: 'Postes', critical: false },
        { url: '/api/rolls/', name: 'Rouleaux', critical: false }
    ];
    
    let criticalOk = true;
    let allOk = true;
    
    for (const endpoint of endpoints) {
        try {
            const startTime = Date.now();
            const response = await fetch(endpoint.url, {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const responseTime = Date.now() - startTime;
            
            if (response.ok) {
                logDebug(`✅ ${endpoint.name} (${responseTime}ms)`, 'success');
            } else {
                logDebug(`❌ ${endpoint.name}: HTTP ${response.status}`, 'error');
                allOk = false;
                if (endpoint.critical) criticalOk = false;
            }
        } catch (error) {
            logDebug(`❌ ${endpoint.name}: ${error.message}`, 'error');
            allOk = false;
            if (endpoint.critical) criticalOk = false;
        }
    }
    
    // Test 4: Test de sauvegarde
    if (criticalOk && window.api) {
        logDebug('--- Test de sauvegarde ---', 'info');
        try {
            const testData = { test_timestamp: Date.now() };
            await window.api.saveToSession(testData);
            logDebug('✅ Test de sauvegarde réussi', 'success');
        } catch (error) {
            logDebug('❌ Échec du test de sauvegarde', 'error');
        }
    }
    
    // Résumé final
    logDebug('--- Résumé ---', 'info');
    if (coreOk && criticalOk) {
        logDebug('✅ Système opérationnel', 'success');
        updateSyncStatus('connected');
    } else if (coreOk && !criticalOk) {
        logDebug('⚠️ Problème de connexion API', 'warning');
        updateSyncStatus('error');
    } else {
        logDebug('❌ Système non initialisé', 'error');
        updateSyncStatus('disconnected');
    }
};

window.testStateManager = function() {
    logDebug('Test StateManager & Core V2', 'info');
    
    // Test StateManager
    if (!window.stateManager) {
        logDebug('❌ StateManager non trouvé!', 'error');
        return;
    }
    logDebug('✅ StateManager disponible', 'success');
    
    // Test CommandBus
    if (!window.commandBus) {
        logDebug('❌ CommandBus non trouvé!', 'error');
    } else {
        logDebug('✅ CommandBus disponible', 'success');
        const commands = window.commandBus.getCommands();
        logDebug(`📝 ${commands.length} commandes enregistrées`, 'info');
        console.log('Commandes disponibles:', commands);
    }
    
    // Test SyncEngine
    if (!window.syncEngine) {
        logDebug('❌ SyncEngine non trouvé!', 'error');
    } else {
        logDebug('✅ SyncEngine disponible', 'success');
        const syncState = window.syncEngine.getSyncState();
        logDebug(`📊 Sync: ${syncState.pending} en attente, ${syncState.failed} échoués`, 'info');
    }
    
    // Test EventBus
    if (!window.eventBus) {
        logDebug('❌ EventBus non trouvé!', 'error');
    } else {
        logDebug('✅ EventBus disponible', 'success');
    }
    
    // Test ValidationEngine
    if (!window.validationEngine) {
        logDebug('❌ ValidationEngine non trouvé!', 'error');
    } else {
        logDebug('✅ ValidationEngine disponible', 'success');
    }
    
    // Test API V2
    if (!window.api || !window.apiV2) {
        logDebug('❌ API V2 non trouvée!', 'error');
    } else {
        logDebug('✅ API V2 disponible', 'success');
    }
    
    // Afficher l'état actuel
    const state = window.stateManager.getState();
    logDebug('--- État actuel ---', 'info');
    
    // Afficher les namespaces avec plus de détails
    const namespaces = {
        'shift': 'Données du poste',
        'of': 'Ordres de fabrication',
        'roll': 'Données rouleau',
        'profile': 'Profil sélectionné',
        'qc': 'Contrôle qualité',
        'production': 'Production'
    };
    
    Object.entries(namespaces).forEach(([key, label]) => {
        const value = state[key];
        if (value && typeof value === 'object') {
            const count = Object.keys(value).length;
            if (count > 0) {
                logDebug(`✅ ${label}: ${count} propriétés`, 'success');
                // Afficher quelques valeurs clés
                if (key === 'shift' && value.operatorId) {
                    logDebug(`  → Opérateur: ${value.operatorId}`, 'info');
                }
                if (key === 'of' && value.targetLength) {
                    logDebug(`  → Longueur cible: ${value.targetLength}m`, 'info');
                }
                if (key === 'roll' && value.measurements) {
                    const measureCount = Object.keys(value.measurements || {}).length;
                    logDebug(`  → ${measureCount} mesures d'épaisseur`, 'info');
                }
            } else {
                logDebug(`⚠️ ${label}: vide`, 'warning');
            }
        } else {
            logDebug(`⚠️ ${label}: non initialisé`, 'warning');
        }
    });
    
    // Test de lecture/écriture
    logDebug('--- Test lecture/écriture ---', 'info');
    const testValue = Date.now();
    window.stateManager.setState('test.debug', testValue, 'system');
    const readValue = window.stateManager.getState('test.debug');
    if (readValue === testValue) {
        logDebug('✅ Test lecture/écriture réussi', 'success');
    } else {
        logDebug('❌ Échec du test lecture/écriture', 'error');
    }
    
    console.log('État complet:', state);
};

window.clearSession = async function() {
    if (!confirm('⚠️ Êtes-vous sûr de vouloir vider toute la session ?')) {
        return;
    }
    
    logDebug('Suppression de la session...', 'warning');
    
    try {
        // Utiliser PATCH pour vider la session
        const response = await fetch('/api/session/', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                profile_id: null,
                shift_id: null,
                operator_id: null,
                shift_date: null,
                vacation: null,
                start_time: null,
                end_time: null,
                machine_started_start: null,
                machine_started_end: null,
                length_start: null,
                length_end: null,
                comment: null,
                of_en_cours: null,
                target_length: null,
                of_decoupe: null,
                roll_number: null,
                quality_control: null,
                checklist_responses: null,
                wound_length_ok: 0,
                wound_length_nok: 0,
                wound_length_total: 0
            })
        });
        
        if (response.ok) {
            logDebug('✅ Session vidée avec succès!', 'success');
            
            // Recharger la page après 1 seconde
            setTimeout(() => {
                logDebug('Rechargement de la page...', 'info');
                window.location.reload();
            }, 1000);
        } else {
            logDebug(`❌ Erreur suppression session: ${response.status} ${response.statusText}`, 'error');
        }
    } catch (error) {
        logDebug('❌ Erreur réseau: ' + error.message, 'error');
    }
};

// Helper
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : window.CSRF_TOKEN || '';
}