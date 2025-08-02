/**
 * Point d'entrée principal V3
 * Initialisation et configuration globale
 */

// Mode debug
const DEBUG = localStorage.getItem('debug') === 'true';

// Logger conditionnel
function debug(message, data = null) {
    if (!DEBUG) return;
    
    const time = new Date().toTimeString().split(' ')[0];
    if (data) {
        console.log(`[${time}] ${message}`, data);
    } else {
        console.log(`[${time}] ${message}`);
    }
}

// Notification système
function showNotification(type, message) {
    // Affichage basique en console pour l'instant
    if (type === 'error') {
        console.error(message);
    } else if (DEBUG) {
        console.info(`[${type.toUpperCase()}] ${message}`);
    }
}

// Export global
window.debug = debug;
window.showNotification = showNotification;

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    debug('✅ V3 System ready');
    debug('📊 Session data:', window.sessionData);
    
    // Alpine.js devrait être initialisé automatiquement
    // Les composants se chargeront via x-data
});

