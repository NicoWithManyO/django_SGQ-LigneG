/**
 * Initialisation spécifique à la page Production V2
 */

// ===== FONCTION TOGGLE CARDS =====
window.toggleCardBody = function(header) {
    const card = header.parentElement;
    const body = card.querySelector('.v2-card-body');
    const chevron = header.querySelector('i[class*="bi-chevron"]');
    
    if (body.style.display === 'none') {
        body.style.display = 'block';
        // Changer la classe pour chevron vers le bas
        chevron.classList.remove('bi-chevron-up');
        chevron.classList.add('bi-chevron-down');
    } else {
        body.style.display = 'none';
        // Changer la classe pour chevron vers le haut
        chevron.classList.remove('bi-chevron-down');
        chevron.classList.add('bi-chevron-up');
    }
};

window.toggleRouleau = function() {
    const qualityBlock = document.getElementById('quality-control-block');
    const chevron = document.querySelector('#rolls-container i[class*="bi-chevron"]');
    
    if (qualityBlock.style.display === 'none') {
        qualityBlock.style.display = 'flex';
        // Changer la classe pour chevron vers le bas
        chevron.classList.remove('bi-chevron-up');
        chevron.classList.add('bi-chevron-down');
    } else {
        qualityBlock.style.display = 'none';
        // Changer la classe pour chevron vers le haut
        chevron.classList.remove('bi-chevron-down');
        chevron.classList.add('bi-chevron-up');
    }
};

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

// Fonctions de test et debug
window.testConnection = async function() {
    try {
        const response = await fetch('/api/session/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        
        if (response.ok) {
            console.log('✅ Connection OK');
            updateSyncStatus('connected');
            showNotification('Connection réussie', 'success');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Connection failed:', error);
        updateSyncStatus('error');
        showNotification('Erreur de connection', 'error');
    }
};

window.testSession = async function() {
    try {
        const data = await window.api.getSession();
        console.log('📦 Session data:', data);
        showNotification('Session chargée - voir console', 'info');
    } catch (error) {
        console.error('❌ Session error:', error);
        showNotification('Erreur session', 'error');
    }
};

window.testStateManager = function() {
    if (!window.stateManager) {
        console.error('StateManager not initialized');
        return;
    }
    
    const state = window.stateManager.getState();
    console.log('🎯 Current state:', state);
    
    // Test set/get
    window.stateManager.setState('test.value', Date.now(), 'user');
    console.log('Test value:', window.stateManager.getState('test.value'));
    
    showNotification('State affiché dans la console', 'info');
};

window.clearSession = async function() {
    if (!confirm('Êtes-vous sûr de vouloir vider la session ?')) return;
    
    try {
        await fetch('/api/session/', {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        showNotification('Session vidée - rechargement...', 'warning');
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        console.error('Clear session error:', error);
        showNotification('Erreur lors du vidage', 'error');
    }
};

// Console de debug
window.toggleDebugConsole = function() {
    const console = document.getElementById('debug-console');
    if (console) {
        console.classList.toggle('d-none');
    }
};

// Mise à jour du statut de synchronisation
function updateSyncStatus(status) {
    const badge = document.getElementById('sync-status-badge');
    if (!badge) return;
    
    const statuses = {
        connected: {
            class: 'bg-success',
            icon: 'bi-cloud-check',
            text: 'Connecté'
        },
        syncing: {
            class: 'bg-warning',
            icon: 'bi-cloud-upload',
            text: 'Synchronisation...'
        },
        error: {
            class: 'bg-danger',
            icon: 'bi-cloud-slash',
            text: 'Erreur'
        },
        disconnected: {
            class: 'bg-secondary',
            icon: 'bi-cloud-slash',
            text: 'Déconnecté'
        }
    };
    
    const config = statuses[status] || statuses.disconnected;
    
    badge.className = `badge ${config.class}`;
    badge.innerHTML = `<i class="bi ${config.icon}"></i> ${config.text}`;
}

// Notifications
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container') || createNotificationContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alert);
    
    // Auto-dismiss après 5 secondes
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 9999;';
    document.body.appendChild(container);
    return container;
}

// Helpers
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

// Surveillance du SyncEngine
function monitorSyncEngine() {
    if (!window.syncEngine) return;
    
    setInterval(() => {
        const state = window.syncEngine.getSyncState();
        
        if (state.syncing > 0) {
            updateSyncStatus('syncing');
        } else if (state.failed > 0) {
            updateSyncStatus('error');
        } else if (state.lastSyncTime && Date.now() - state.lastSyncTime < 10000) {
            updateSyncStatus('connected');
        }
    }, 2000);
}

// Logs personnalisés dans la console de debug
function setupDebugLogging() {
    const debugOutput = document.getElementById('debug-output');
    if (!debugOutput) return;
    
    // Intercepter les logs
    const originalLog = console.log;
    console.log = function(...args) {
        originalLog.apply(console, args);
        
        if (debugOutput) {
            const entry = document.createElement('div');
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${args.join(' ')}`;
            debugOutput.appendChild(entry);
            debugOutput.scrollTop = debugOutput.scrollHeight;
            
            // Limiter à 100 lignes
            while (debugOutput.children.length > 100) {
                debugOutput.removeChild(debugOutput.firstChild);
            }
        }
    };
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    // Configurer la surveillance
    monitorSyncEngine();
    setupDebugLogging();
    
    // État initial
    updateSyncStatus('disconnected');
    
    console.log('🎮 Production V2 initialized');
});