/**
 * Utilitaires partagés pour les grilles de rouleaux
 */

// Déterminer si une ligne est une ligne de mesure
export function isMeasurementRow(row) {
    // Première mesure à 3m, puis tous les 5m
    if (row === 3) return true;
    if (row > 3 && (row - 3) % 5 === 0) return true;
    return false;
}

// Créer un input d'épaisseur
export function createThicknessInput(row, col) {
    const input = document.createElement('input');
    input.type = 'number';
    input.step = '0.01';
    input.min = '0';
    input.className = 'thickness-input';
    input.placeholder = '-';
    input.dataset.row = row;
    input.dataset.col = col;
    input.id = `thickness-${row}-${col}`;
    
    return input;
}

// Restaurer les données dans la grille
export function restoreGridData(measurements, defects, updateDefectDisplay) {
    // Restaurer les mesures
    Object.entries(measurements).forEach(([key, value]) => {
        const [row, col] = key.split('-');
        const input = document.getElementById(`thickness-${row}-${col}`);
        if (input) {
            input.value = value;
            input.classList.add('v2-input-filled');
        }
    });
    
    // Restaurer les défauts
    Object.entries(defects).forEach(([key, defectList]) => {
        const [row, col] = key.split('-');
        if (defectList && defectList.length > 0) {
            updateDefectDisplay(parseInt(row), parseInt(col));
        }
    });
}

// Générer une valeur d'épaisseur aléatoire
export function generateRandomThickness(min = 3, max = 9) {
    return (Math.random() * (max - min) + min).toFixed(2);
}

// Calculer le nombre de lignes en fonction de la longueur cible
export function calculateRows(targetLength, maxRows = 50) {
    return Math.min(targetLength, maxRows);
}

// Export pour utilisation globale si pas de support des modules
if (typeof window !== 'undefined') {
    window.rollUtils = {
        isMeasurementRow,
        createThicknessInput,
        restoreGridData,
        generateRandomThickness,
        calculateRows
    };
}