/**
 * Constantes globales pour l'application SGQ V2
 */

// Couleurs principales
export const COLORS = {
    primary: '#0d6efd',
    danger: '#dc3545',
    warning: '#fd7e14',
    success: '#198754',
    info: '#0dcaf9',
    secondary: '#6c757d',
    
    // Couleurs spécifiques
    borderLight: '#dee2e6',
    borderInput: '#90caf9',
    backgroundInput: '#e3f2fd',
    backgroundHover: '#f8f9fa',
    backgroundDangerLight: '#dc35451a',
    backgroundWarningLight: '#fd7e141a',
    backgroundPrimaryLight: '#0d6efd1a'
};

// Intervalles de mesure du rouleau
export const ROLL_MEASUREMENTS = {
    firstMeasurement: 3,  // Première mesure à 3m
    interval: 5,          // Puis tous les 5m
    maxRows: 50          // Maximum de lignes à afficher
};

// Délais et timeouts
export const DELAYS = {
    syncDelay: 300,       // Délai de synchronisation (ms)
    debounceDelay: 300,   // Délai de debounce (ms)
    loadDelay: 100,       // Délai de chargement initial (ms)
    cacheTimeout: 300000  // Timeout du cache (5 minutes)
};

// Tailles et dimensions
export const SIZES = {
    defectButtonSize: 16,     // Taille du bouton défaut (px)
    badgeFontSize: '0.65rem', // Taille de police des badges
    inputThicknessWidth: '40%', // Largeur des inputs d'épaisseur
    inputThicknessHeight: '60%' // Hauteur des inputs d'épaisseur
};

// Angles de rotation
export const ROTATIONS = {
    defectBadgesFull: -45,    // Rotation complète pour badges avec input
    defectBadgesHalf: -22.5   // Rotation réduite pour badges sans input
};