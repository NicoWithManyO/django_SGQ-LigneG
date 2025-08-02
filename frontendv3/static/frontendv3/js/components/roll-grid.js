/**
 * Composant Alpine.js : Grille du Rouleau
 * Gestion complète de la grille, défauts et épaisseurs
 */

function rollGrid() {
    const savedData = window.sessionData?.roll || {};
    const ofData = window.sessionData?.of || {};
    
    return {
        // État local
        targetLength: ofData.targetLength || 30,
        defects: savedData.defects || {},
        thicknessValues: savedData.thicknessValues || {},
        rattrapages: savedData.rattrapages || {},
        profileSpecs: null,
        thicknessSpec: null,
        
        // État de la popup
        showPopup: false,
        popupX: 0,
        popupY: 0,
        currentCell: null,
        defectTypes: [],
        
        // Constantes de grille
        CELLS_PER_ROW: 7,
        
        // Getters calculés
        get totalRows() {
            return this.targetLength; // 1 ligne = 1 mètre
        },
        
        get gridCells() {
            const cells = [];
            for (let row = 0; row < this.totalRows; row++) {
                const meter = row + 1;
                
                // Si longueur < 3m, mettre les épaisseurs au mètre 1
                // Sinon, les mettre aux mètres 3, 8, 13, etc.
                let hasThickness = false;
                if (this.targetLength < 3) {
                    hasThickness = meter === 1;
                } else {
                    hasThickness = meter >= 3 && (meter - 3) % 5 === 0;
                }
                
                // 7 colonnes par ligne
                for (let col = 0; col < this.CELLS_PER_ROW; col++) {
                    cells.push({
                        row: row,
                        col: col,
                        meter: meter,
                        // Inputs d'épaisseur: colonnes 0,1,2 et 4,5,6 (pas la colonne 3 du milieu)
                        isThickness: hasThickness && col !== 3
                    });
                }
            }
            return cells;
        },
        
        // Initialisation
        init() {
            debug('Roll grid initialized');
            
            // Exposer les fonctions utiles globalement
            window.rollGridUtils = {
                fillRandom: () => this.fillRandomThickness(),
                clearAll: () => this.clearAllThickness(),
                fillAll: (value) => this.fillAllThickness(value),
                setLength: (length) => {
                    this.targetLength = length;
                    // Propager le changement
                    window.dispatchEvent(new CustomEvent('target-length-changed', {
                        detail: { length: length }
                    }));
                    // Sauvegarder
                    this.saveToSession();
                    debug(`Target length reset to ${length}m`);
                }
            };
            
            // Écouter les changements de longueur cible
            window.addEventListener('target-length-changed', (event) => {
                this.targetLength = event.detail.length || 30;
                debug('Target length updated:', this.targetLength);
            });
            
            // Écouter les changements de profil
            window.addEventListener('profile-changed', (event) => {
                this.profileSpecs = event.detail.profileSpecs || null;
                // Extraire la spec épaisseur
                if (this.profileSpecs) {
                    this.thicknessSpec = this.profileSpecs.find(spec => spec.name === 'Épaisseur');
                    debug('Thickness spec loaded:', this.thicknessSpec);
                    
                    // Revalider toutes les épaisseurs existantes
                    this.$nextTick(() => {
                        this.validateExistingThickness();
                    });
                }
            });
            
            // Exposer les fonctions globalement pour les tests
            window.fillAllThickness = (value) => this.fillAllThickness(value);
            window.fillRandomThickness = () => this.fillRandomThickness();
            
            // Observer les changements de thicknessValues pour sauvegarder
            this.$watch('thicknessValues', () => {
                this.saveToSession();
            }, { deep: true });
            
            // Charger les types de défauts depuis l'API
            this.loadDefectTypes();
            
            // Appliquer la validation sur les valeurs existantes au prochain tick
            this.$nextTick(() => {
                this.validateExistingThickness();
            });
        },
        
        // Charger les types de défauts depuis l'API
        async loadDefectTypes() {
            try {
                const response = await fetch('/api/defect-types/');
                const data = await response.json();
                
                if (data.success) {
                    // Filtrer pour retirer "Epaisseurs" du sélecteur
                    this.defectTypes = data.defects.filter(d => d.name !== 'Epaisseurs');
                    debug('Loaded defect types:', this.defectTypes);
                } else {
                    console.error('Erreur chargement défauts:', data.error);
                }
            } catch (error) {
                console.error('Erreur chargement défauts:', error);
            }
        },
        
        // Sauvegarder dans la session
        saveToSession() {
            const data = {
                defects: this.defects,
                thicknessValues: this.thicknessValues,
                rattrapages: this.rattrapages
            };
            window.saveToSession('roll', data);
        },
        
        // Utilitaire pour générer une clé unique pour une cellule
        getCellKey(row, col) {
            return `${row}-${col}`;
        },
        
        // Gestion de la saisie numérique pour les épaisseurs
        handleThicknessKeypress(event) {
            const char = String.fromCharCode(event.which);
            const value = event.target.value;
            
            // Autoriser: chiffres, virgule, point (mais un seul)
            if (!/[0-9,.]/.test(char)) {
                event.preventDefault();
                return;
            }
            
            // Empêcher multiple virgules/points
            if ((char === ',' || char === '.') && /[,.]/.test(value)) {
                event.preventDefault();
            }
        },
        
        // Gérer le blur sur input d'épaisseur
        handleThicknessBlur(row, col, event) {
            const key = this.getCellKey(row, col);
            let value = this.thicknessValues[key];
            
            if (!value || value.trim() === '') {
                delete this.thicknessValues[key];
                // Retirer toutes les classes de validation
                event.target.classList.remove('thickness-min', 'thickness-alert-min', 'thickness-nominal', 'thickness-alert-max', 'thickness-max');
                return;
            }
            
            // Remplacer virgule par point pour Django
            value = value.replace(',', '.');
            
            // Valider le format numérique
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                // Formater la valeur
                this.thicknessValues[key] = numValue.toString();
                
                // D'abord appliquer la validation visuelle
                this.applyThicknessValidation(event.target, numValue);
                
                // Ensuite vérifier si c'est un rattrapage selon les specs du profil
                if (this.thicknessSpec && this.thicknessSpec.value_min !== null && numValue < this.thicknessSpec.value_min) {
                    // Ne créer un rattrapage que s'il n'y en a pas déjà un
                    if (!this.rattrapages[key]) {
                        this.rattrapages[key] = numValue.toString();
                        delete this.thicknessValues[key];
                        // Forcer la mise à jour de l'input
                        event.target.value = '';
                        // Retirer toutes les classes de validation pour que la case reste bleue
                        event.target.classList.remove('thickness-min', 'thickness-alert-min', 'thickness-nominal', 'thickness-alert-max', 'thickness-max');
                    }
                    // Si il y a déjà un rattrapage, garder la valeur dans l'input
                }
            } else {
                // Valeur invalide, supprimer
                delete this.thicknessValues[key];
            }
        },
        
        // Appliquer la validation visuelle sur l'épaisseur
        applyThicknessValidation(input, value) {
            // Retirer toutes les classes de validation
            input.classList.remove('thickness-min', 'thickness-alert-min', 'thickness-nominal', 'thickness-alert-max', 'thickness-max');
            
            if (!this.thicknessSpec) {
                debug('No thickness spec available');
                return;
            }
            
            const spec = this.thicknessSpec;
            debug('Validating thickness:', value, 'against spec:', spec);
            
            // Appliquer la classe selon les seuils
            if (spec.value_min !== null && value < spec.value_min) {
                input.classList.add('thickness-min');
                debug('Applied thickness-min');
            } else if (spec.value_min_alert !== null && value < spec.value_min_alert) {
                input.classList.add('thickness-alert-min');
                debug('Applied thickness-alert-min');
            } else if (spec.value_max !== null && value > spec.value_max) {
                input.classList.add('thickness-max');
                debug('Applied thickness-max');
            } else if (spec.value_max_alert !== null && value > spec.value_max_alert) {
                input.classList.add('thickness-alert-max');
                debug('Applied thickness-alert-max');
            } else {
                // Dans la plage nominale
                input.classList.add('thickness-nominal');
                debug('Applied thickness-nominal');
            }
        },
        
        
        // Obtenir le rattrapage d'une cellule
        getRattrapage(row, col) {
            const key = this.getCellKey(row, col);
            return this.rattrapages[key] || null;
        },
        
        // Supprimer un rattrapage
        removeRattrapage(row, col) {
            const key = this.getCellKey(row, col);
            delete this.rattrapages[key];
            this.saveToSession();
        },
        
        // Valider les épaisseurs existantes
        validateExistingThickness() {
            this.gridCells.forEach(cell => {
                if (cell.isThickness) {
                    const key = this.getCellKey(cell.row, cell.col);
                    const input = this.$el.querySelector(`[data-row="${cell.row}"][data-col="${cell.col}"] .thickness-input`);
                    
                    if (input) {
                        if (input.value && input.value.trim() !== '') {
                            const value = parseFloat(input.value);
                            if (!isNaN(value)) {
                                this.applyThicknessValidation(input, value);
                            }
                        } else {
                            // Retirer toutes les classes si l'input est vide - toujours bleu
                            input.classList.remove('thickness-min', 'thickness-alert-min', 'thickness-nominal', 'thickness-alert-max', 'thickness-max');
                        }
                    }
                }
            });
        },
        
        // Remplir toutes les cases d'épaisseur avec une valeur
        fillAllThickness(value = '2.5') {
            this.gridCells.forEach(cell => {
                if (cell.isThickness) {
                    const key = this.getCellKey(cell.row, cell.col);
                    this.thicknessValues[key] = value;
                }
            });
            
            // Appliquer la validation et déclencher les rattrapages
            this.$nextTick(() => {
                const inputs = this.$el.querySelectorAll('.thickness-input');
                inputs.forEach(input => {
                    if (input.value) {
                        // Déclencher l'événement blur pour activer la logique de rattrapage
                        const event = new Event('blur', { bubbles: true });
                        input.dispatchEvent(event);
                    }
                });
            });
            
            debug(`Filled thickness inputs with value: ${value}`);
        },
        
        // Remplir avec des valeurs aléatoires réalistes
        fillRandomThickness() {
            // Si on a des specs de profil, utiliser les limites
            let minValue = 2.3;
            let maxValue = 2.7;
            let nominal = 2.5;
            
            if (this.thicknessSpec) {
                minValue = this.thicknessSpec.value_min || 2.3;
                maxValue = this.thicknessSpec.value_max || 2.7;
                nominal = this.thicknessSpec.value_nominal || 2.5;
            }
            
            this.gridCells.forEach(cell => {
                if (cell.isThickness) {
                    const key = this.getCellKey(cell.row, cell.col);
                    
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
                    
                    this.thicknessValues[key] = randomValue;
                }
            });
            
            // Appliquer la validation et déclencher les rattrapages
            this.$nextTick(() => {
                const inputs = this.$el.querySelectorAll('.thickness-input');
                inputs.forEach(input => {
                    if (input.value) {
                        // Déclencher l'événement blur pour activer la logique de rattrapage
                        const event = new Event('blur', { bubbles: true });
                        input.dispatchEvent(event);
                    }
                });
            });
            
            debug('Filled thickness inputs with realistic random values');
        },
        
        // Vider toutes les épaisseurs et rattrapages
        clearAllThickness() {
            // Vider toutes les épaisseurs
            this.thicknessValues = {};
            
            // Vider tous les rattrapages
            this.rattrapages = {};
            
            // Réinitialiser les classes de validation
            this.$nextTick(() => {
                const inputs = this.$el.querySelectorAll('.thickness-input');
                inputs.forEach(input => {
                    input.value = '';
                    input.classList.remove('thickness-min', 'thickness-alert-min', 
                                         'thickness-nominal', 'thickness-alert-max', 
                                         'thickness-max');
                });
            });
            
            // Réinitialiser les défauts
            this.defects = {};
            this.$el.querySelectorAll('.defect-count').forEach(el => el.textContent = '0');
            
            this.saveToSession();
            showNotification('info', 'Grille de rouleau réinitialisée');
        },
        
        // Afficher la popup de sélection de défauts
        showDefectPopup(row, col, event) {
            this.currentCell = { row, col };
            
            // Position centrée sous le curseur (position fixe)
            this.popupX = event.clientX - 100; // 100 = moitié de la largeur min de la popup
            this.popupY = event.clientY + 10; // 10px sous le curseur
            
            // S'assurer que la popup reste dans les limites de la fenêtre
            const maxX = window.innerWidth - 200; // 200 = largeur min de la popup
            this.popupX = Math.max(0, Math.min(this.popupX, maxX));
            
            this.showPopup = true;
        },
        
        // Ajouter un défaut à une cellule
        addDefect(defectName) {
            if (!this.currentCell) return;
            
            const key = this.getCellKey(this.currentCell.row, this.currentCell.col);
            if (!this.defects[key]) {
                this.defects[key] = [];
            }
            
            // Éviter les doublons dans la même cellule
            if (!this.defects[key].includes(defectName)) {
                this.defects[key].push(defectName);
                debug(`Added defect "${defectName}" to cell ${key}`);
                this.saveToSession();
            }
            
            this.showPopup = false;
            this.currentCell = null;
        },
        
        // Retirer un défaut d'une cellule
        removeDefect(row, col, defectName) {
            const key = this.getCellKey(row, col);
            if (this.defects[key]) {
                this.defects[key] = this.defects[key].filter(d => d !== defectName);
                if (this.defects[key].length === 0) {
                    delete this.defects[key];
                }
                debug(`Removed defect "${defectName}" from cell ${key}`);
                this.saveToSession();
            }
        },
        
        // Obtenir les défauts d'une cellule
        getDefects(row, col) {
            const key = this.getCellKey(row, col);
            return this.defects[key] || [];
        },
        
        // Compter les défauts sur tout le rouleau
        getDefectCount(defectName) {
            let count = 0;
            Object.values(this.defects).forEach(cellDefects => {
                count += cellDefects.filter(d => d === defectName).length;
            });
            return count;
        },
        
        // Obtenir la classe CSS pour un défaut
        getDefectClass(defectName) {
            const defectType = this.defectTypes.find(d => d.name === defectName);
            return defectType ? `bg-${defectType.color}` : 'bg-secondary';
        },
        
        
    };
}

// Export global pour Alpine
window.rollGrid = rollGrid;