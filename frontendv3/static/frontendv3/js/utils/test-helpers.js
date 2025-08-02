/**
 * Utilitaires de test pour remplissage automatique
 */

// Fonction pour remplir le contrôle qualité avec des valeurs aléatoires conformes
function fillQualityControlWithRandomValues(component) {
    
    // Récupérer les specs du profil
    let micromaireSpec = null;
    let masseSurfSpec = null;
    let extraitSecSpec = null;
    
    if (component.profileSpecs && component.profileSpecs.length > 0) {
        micromaireSpec = component.profileSpecs.find(s => 
            s.name === 'micromaire_g' || 
            s.name === 'micromaire' || 
            s.name === 'Micronaire'
        );
        masseSurfSpec = component.profileSpecs.find(s => 
            s.name === 'masse_surfacique' || 
            s.name === 'Masse Surfacique'
        );
        extraitSecSpec = component.profileSpecs.find(s => 
            s.name === 'extrait_sec' || 
            s.name === 'Extrait Sec'
        );
    }
    
    // Fonction helper pour générer une valeur dans les specs
    const getRandomInSpec = (spec, defaultMin, defaultMax, decimals = 2) => {
        if (!spec) {
            const value = defaultMin + Math.random() * (defaultMax - defaultMin);
            return parseFloat(value.toFixed(decimals));
        }
        
        const min = parseFloat(spec.value_min) || defaultMin;
        const max = parseFloat(spec.value_max) || defaultMax;
        const target = parseFloat(spec.value_target) || (min + max) / 2;
        
        // Générer une valeur proche de la cible (distribution normale simulée)
        const range = (max - min) * 0.3; // 30% de la plage pour la variation
        let value = target + (Math.random() - 0.5) * range;
        
        // S'assurer qu'on reste dans les limites
        value = Math.max(min, Math.min(max, value));
        
        return parseFloat(value.toFixed(decimals));
    };
    
    // Remplir Micromaire avec variation légère entre les mesures
    const baseMicromaireG = getRandomInSpec(micromaireSpec, 3.5, 4.5, 2);
    const baseMicromaireD = getRandomInSpec(micromaireSpec, 3.5, 4.5, 2);
    
    for (let i = 0; i < 3; i++) {
        // Variation de ±0.05 autour de la valeur de base
        component.micromaireG[i] = (baseMicromaireG + (Math.random() - 0.5) * 0.1).toFixed(2);
        component.micromaireD[i] = (baseMicromaireD + (Math.random() - 0.5) * 0.1).toFixed(2);
    }
    
    // Remplir Masse Surfacique avec variation cohérente
    const baseMasseSurf = getRandomInSpec(masseSurfSpec, 0.8, 1.2, 4);
    
    // Gauche avec légère variation
    component.masseSurfaciqueGG = (baseMasseSurf + (Math.random() - 0.5) * 0.05).toFixed(4);
    component.masseSurfaciqueGC = (baseMasseSurf + (Math.random() - 0.5) * 0.05).toFixed(4);
    
    // Droite avec légère variation
    component.masseSurfaciqueDC = (baseMasseSurf + (Math.random() - 0.5) * 0.05).toFixed(4);
    component.masseSurfaciqueDD = (baseMasseSurf + (Math.random() - 0.5) * 0.05).toFixed(4);
    
    // Extrait sec
    component.extraitSec = getRandomInSpec(extraitSecSpec, 18, 22, 2).toString();
    const now = new Date();
    component.extraitTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    // LOI donnée (80% de chance)
    component.loi = Math.random() > 0.2;
    if (component.loi) {
        const loiTime = new Date(now.getTime() + 5 * 60000); // 5 minutes après
        component.loiTime = `${loiTime.getHours().toString().padStart(2, '0')}:${loiTime.getMinutes().toString().padStart(2, '0')}`;
    }
    
    // Forcer le recalcul des moyennes et du statut
    component.moyenneMicromaireG = component.calculateAverage(component.micromaireG);
    component.moyenneMicromaireD = component.calculateAverage(component.micromaireD);
    component.moyenneMasseSurfaciqueG = component.calculateAverageMasse('G');
    component.moyenneMasseSurfaciqueD = component.calculateAverageMasse('D');
    
    component.checkQCStatus();
    component.updateGlobalAverages();
    component.autoSave();
    
    showNotification('success', 'Contrôle qualité rempli avec des valeurs conformes');
}

// Fonction pour effacer toute la grille de rouleau
function clearRollGrid(component) {
    // Vider toutes les épaisseurs
    component.thicknessValues = {};
    
    // Vider tous les rattrapages
    component.rattrapages = {};
    
    // Réinitialiser les classes de validation
    component.$nextTick(() => {
        const inputs = component.$el.querySelectorAll('.thickness-input');
        inputs.forEach(input => {
            input.value = '';
            input.classList.remove('thickness-min', 'thickness-alert-min', 
                                 'thickness-nominal', 'thickness-alert-max', 
                                 'thickness-max');
        });
    });
    
    // Réinitialiser les défauts
    component.defects = {};
    component.$el.querySelectorAll('.defect-count').forEach(el => el.textContent = '0');
    
    // Sauvegarder en session
    component.saveToSession();
    
    showNotification('info', 'Grille de rouleau réinitialisée');
}

// Fonction pour remplir la grille avec des valeurs aléatoires
function fillRollGridRandom(component) {
    // Si on a des specs de profil, utiliser les limites
    let minValue = 2.3;
    let maxValue = 2.7;
    let nominal = 2.5;
    
    if (component.thicknessSpec) {
        minValue = component.thicknessSpec.value_min || 2.3;
        maxValue = component.thicknessSpec.value_max || 2.7;
        nominal = component.thicknessSpec.value_nominal || 2.5;
    }
    
    component.gridCells.forEach(cell => {
        if (cell.isThickness) {
            const key = component.getCellKey(cell.row, cell.col);
            
            // 80% de chance d'être proche de la valeur nominale
            // 20% de chance d'être dans les extrêmes
            const chance = Math.random();
            let randomValue;
            
            if (chance < 0.8) {
                // Valeur proche du nominal (±0.05)
                const variation = (Math.random() - 0.5) * 0.1;
                randomValue = (nominal + variation).toFixed(2);
            } else if (chance < 0.9) {
                // Valeur basse
                randomValue = (minValue + Math.random() * 0.1).toFixed(2);
            } else {
                // Valeur haute
                randomValue = (maxValue - Math.random() * 0.1).toFixed(2);
            }
            
            component.thicknessValues[key] = randomValue;
            
            // Mettre à jour visuellement avec un délai
            setTimeout(() => {
                const input = component.$el.querySelector(`#${cell.id}`);
                if (input) {
                    input.value = randomValue;
                    input.dispatchEvent(new Event('blur'));
                }
            }, Math.random() * 500);
        }
    });
    
    showNotification('success', 'Valeurs aléatoires générées dans les tolérances');
}

// Exposer les fonctions de test
window.testHelpers = {
    fillQualityControl: fillQualityControlWithRandomValues,
    clearRollGrid: clearRollGrid,
    fillRollGrid: fillRollGridRandom
};