/**
 * Composant Alpine.js : Grille du Rouleau
 * Gestion complète de la grille, défauts et épaisseurs
 */

function rollGrid() {
    const savedData = window.sessionData?.roll || {};
    const ofData = window.sessionData?.of || {};
    
    return {
        // Mixin
        ...window.sessionMixin,
        // État local
        targetLength: ofData.targetLength || 30,
        defects: savedData.defects || {},
        thicknessValues: savedData.thicknessValues || {},
        rattrapages: savedData.rattrapages || {},
        profileSpecs: null,
        thicknessSpec: null,
        _lastConformityStatus: 'CONFORME', // Pour tracker les changements de statut (initialisé à CONFORME)
        _lastAllFilled: false, // Pour tracker les changements d'état de remplissage
        allDefectTypes: [], // Pour garder tous les types y compris "Epaisseurs"
        grammageStatus: '', // Pour stocker le statut du grammage
        grammage: '--', // Pour stocker la valeur du grammage
        
        // État de la popup
        showPopup: false,
        popupX: 0,
        popupY: 0,
        currentCell: null,
        defectTypes: [],
        
        // Constantes de grille
        CELLS_PER_ROW: 7,
        MIDDLE_COLUMN: 3,  // Colonne centrale qui sépare Gauche/Droite
        
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
            
            // Initialiser le mixin session
            this.initSession();
            
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
                    this.saveRollData();
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
            
            // Écouter l'événement de reset après sauvegarde d'un rouleau
            window.addEventListener('roll:reset', () => {
                debug('Roll reset received - clearing thickness grid');
                this.clearAllThickness();
                // Reset aussi les mètres de rattrapage
                this.catchupCells = new Set();
            });
            
            // Exposer les fonctions globalement pour les tests
            window.fillAllThickness = (value) => this.fillAllThickness(value);
            window.fillRandomThickness = () => this.fillRandomThickness();
            
            // Observer les changements pour auto-save
            // On doit sauvegarder tout l'objet roll d'un coup
            this.$watch(() => ({
                defects: this.defects,
                thicknessValues: this.thicknessValues,
                rattrapages: this.rattrapages
            }), () => {
                this.saveRollData();
            }, { deep: true });
            
            // Observer les changements de thicknessValues pour recalculer la conformité
            this.$watch('thicknessValues', () => {
                // Recalculer la conformité
                this.conformityStatus;
                // Émettre le résumé des NOK (au cas où un rattrapage change)
                window.dispatchEvent(new CustomEvent('nok-summary-changed', {
                    detail: this.getNOKSummary()
                }));
            }, { deep: true });
            
            // Observer les changements de rattrapages
            this.$watch('rattrapages', () => {
                // Recalculer la conformité
                this.conformityStatus;
                // Émettre le résumé des NOK
                window.dispatchEvent(new CustomEvent('nok-summary-changed', {
                    detail: this.getNOKSummary()
                }));
            }, { deep: true });
            
            // Observer les changements de specs
            this.$watch('thicknessSpec', () => {
                // Recalculer la conformité avec les nouvelles specs
                this.conformityStatus;
            });
            
            // Écouter les changements de statut du grammage
            window.addEventListener('grammage:status-changed', (event) => {
                this.grammageStatus = event.detail.status || '';
                this.grammage = event.detail.grammage || '--';
                debug(`Grammage status received: ${this.grammageStatus}`);
                // Forcer le recalcul de la conformité
                this._lastConformityStatus = null;
                this.conformityStatus;
            });
            
            // Récupérer le statut initial du grammage après un délai
            this.$nextTick(() => {
                const stickyBarElement = document.querySelector('[x-data*="stickyBar"]');
                if (stickyBarElement && stickyBarElement._x_dataStack) {
                    const stickyBar = stickyBarElement._x_dataStack[0];
                    this.grammageStatus = stickyBar.grammageStatus || '';
                    this.grammage = stickyBar.grammage || '--';
                    debug('Initial grammage from sticky-bar:', this.grammage, 'status:', this.grammageStatus);
                }
            });
            
            // Charger les types de défauts depuis l'API
            this.loadDefectTypes();
            
            // Exposer l'instance globalement pour l'accès externe
            window.rollGridInstance = this;
            
            // Exposer la méthode getCellInfo pour usage dans les templates
            window.rollGridUtils.getCellInfo = (key) => this.getCellInfo(key);
            
            // Émettre l'événement initial des défauts
            this.$nextTick(() => {
                window.dispatchEvent(new CustomEvent('defects-updated'));
                // Forcer le calcul initial de conformité
                const initialStatus = this.conformityStatus;
                if (initialStatus === 'NON_CONFORME') {
                    // Si on démarre en NON_CONFORME, émettre l'événement
                    window.eventBus.emit(window.eventBus.EVENTS.ROLL_CONFORMITY_CHANGED, { 
                        status: 'NON_CONFORME',
                        previousStatus: 'CONFORME',
                        allThicknessesFilled: this.allThicknessesFilled
                    });
                }
            });
            
            // Appliquer la validation sur les valeurs existantes au prochain tick
            this.$nextTick(() => {
                this.validateExistingThickness();
                // Forcer l'émission initiale du statut de conformité
                const status = this.conformityStatus;
                debug(`Initial conformity status: ${status}, allFilled: ${this.allThicknessesFilled}`);
            });
            
            // Écouter les changements de profil pour récupérer les specs
            window.addEventListener('profile-specs-changed', (event) => {
                this.profileSpecs = event.detail.specifications;
                debug('Profile specs received:', this.profileSpecs);
                // Recalculer la conformité avec les nouvelles specs
                this.conformityStatus;
            });
            
            // Déclencher le calcul initial de conformité après un délai
            this.$nextTick(() => {
                // Forcer l'émission initiale du statut
                const status = this.conformityStatus;
                const allFilled = this.allThicknessesFilled;
                debug(`Forcing initial conformity emit: status=${status}, allFilled=${allFilled}`);
                
                // Forcer l'émission même si les valeurs n'ont pas "changé"
                window.eventBus.emit(window.eventBus.EVENTS.ROLL_CONFORMITY_CHANGED, { 
                    status,
                    previousStatus: null,
                    allThicknessesFilled: allFilled
                });
            });
        },
        
        // Charger les types de défauts depuis l'API
        async loadDefectTypes() {
            try {
                const response = await fetch('/api/defect-types/');
                const data = await response.json();
                
                if (data.success) {
                    // Garder tous les défauts pour avoir accès aux seuils
                    this.allDefectTypes = data.defects;
                    // Filtrer pour retirer "Epaisseurs" du sélecteur uniquement
                    this.defectTypes = data.defects.filter(d => d.name !== 'Epaisseurs');
                    console.log('Loaded all defect types:', this.allDefectTypes);
                    console.log('Filtered defect types for selector:', this.defectTypes);
                    
                    // Vérifier spécifiquement le défaut Epaisseurs
                    const thicknessDefect = this.allDefectTypes.find(d => d.name === 'Epaisseurs');
                    console.log('Thickness defect:', thicknessDefect);
                    
                    // Recalculer la conformité maintenant qu'on a les types
                    this.conformityStatus;
                } else {
                    console.error('Erreur chargement défauts:', data.error);
                }
            } catch (error) {
                console.error('Erreur chargement défauts:', error);
            }
        },
        
        // Sauvegarder dans la session avec debounce
        saveRollData() {
            // Annuler le timeout précédent
            if (this._rollSaveTimeout) {
                clearTimeout(this._rollSaveTimeout);
            }
            
            // Créer un nouveau timeout
            this._rollSaveTimeout = setTimeout(() => {
                const data = {
                    defects: this.defects,
                    thicknessValues: this.thicknessValues,
                    rattrapages: this.rattrapages
                };
                this.saveToSession({ roll: data });
            }, this.DEBOUNCE_DELAY || 300);
        },
        
        // Utilitaire pour générer une clé unique pour une cellule
        getCellKey(row, col) {
            return `${row}-${col}`;
        },
        
        // Helper pour obtenir les infos d'une cellule à partir de sa clé
        getCellInfo(key) {
            const [row, col] = key.split('-').map(Number);
            const meter = row + 1;
            const position = col < this.MIDDLE_COLUMN ? 'G' : 'D';
            return { 
                meter, 
                position, 
                posKey: `${position}${meter}m`,
                row,
                col
            };
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
                    // Si pas de rattrapage existant, créer un
                    if (!this.rattrapages[key]) {
                        // Première valeur NOK -> la déplacer vers rattrapages
                        this.rattrapages[key] = numValue.toString();
                        delete this.thicknessValues[key];
                        // Forcer la mise à jour de l'input
                        event.target.value = '';
                        // Retirer toutes les classes de validation pour que la case reste bleue
                        event.target.classList.remove('thickness-min', 'thickness-alert-min', 'thickness-nominal', 'thickness-alert-max', 'thickness-max');
                    } else {
                        // Il y a déjà un rattrapage (badge rouge)
                        // C'est une tentative de correction, elle reste dans l'input
                        // Ne pas vider l'input dans ce cas
                    }
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
        
        // Gérer la saisie d'un rattrapage
        handleRattrapageBlur(row, col, event) {
            const key = this.getCellKey(row, col);
            let value = event.target.value;
            
            if (!value || value.trim() === '') {
                delete this.rattrapages[key];
                return;
            }
            
            // Remplacer virgule par point
            value = value.replace(',', '.');
            
            // Valider le format numérique
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                this.rattrapages[key] = numValue.toString();
                // La sauvegarde se fait automatiquement via le watch
            } else {
                delete this.rattrapages[key];
            }
        },
        
        // Supprimer un rattrapage
        removeRattrapage(row, col) {
            const key = this.getCellKey(row, col);
            delete this.rattrapages[key];
            // La sauvegarde se fait automatiquement via le watch
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
        
        // Remplir avec des valeurs aléatoires réalistes CONFORMES
        fillRandomThickness() {
            // Si on a des specs de profil, utiliser les limites
            let minValue = 2.3;
            let maxValue = 2.7;
            let nominal = 2.5;
            let minAlert = 2.35;
            let maxAlert = 2.65;
            
            if (this.thicknessSpec) {
                minValue = this.thicknessSpec.value_min || 2.3;
                maxValue = this.thicknessSpec.value_max || 2.7;
                nominal = this.thicknessSpec.value_nominal || 2.5;
                minAlert = this.thicknessSpec.value_min_alert || minValue + (nominal - minValue) * 0.25;
                maxAlert = this.thicknessSpec.value_max_alert || maxValue - (maxValue - nominal) * 0.25;
            }
            
            this.gridCells.forEach(cell => {
                if (cell.isThickness) {
                    const key = this.getCellKey(cell.row, cell.col);
                    
                    // Toujours générer des valeurs CONFORMES (entre min_alert et max_alert)
                    // Centré sur la valeur nominale avec distribution normale simulée
                    let randomValue;
                    
                    // Utiliser Box-Muller pour générer une distribution normale
                    const u1 = Math.random();
                    const u2 = Math.random();
                    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
                    
                    // Centrer sur nominal avec écart-type = (maxAlert - minAlert) / 6
                    // pour que 99.7% des valeurs soient dans la plage
                    const sigma = (maxAlert - minAlert) / 6;
                    randomValue = nominal + z0 * sigma;
                    
                    // S'assurer qu'on reste dans les limites d'alerte
                    randomValue = Math.max(minAlert, Math.min(maxAlert, randomValue));
                    
                    // Arrondir à 2 décimales
                    this.thicknessValues[key] = randomValue.toFixed(2);
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
            
            // Force save after reset
            this.saveRollData();
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
                // La sauvegarde se fait automatiquement via le watch
                // Forcer le recalcul de la conformité
                this._lastConformityStatus = null;
                const newStatus = this.conformityStatus;
                // Émettre l'événement de mise à jour des défauts
                window.dispatchEvent(new CustomEvent('defects-updated'));
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
                // La sauvegarde se fait automatiquement via le watch
                // Forcer le recalcul de la conformité
                this._lastConformityStatus = null;
                const newStatus = this.conformityStatus;
                // Émettre l'événement de mise à jour des défauts
                window.dispatchEvent(new CustomEvent('defects-updated'));
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
        
        // === Méthodes de conformité ===
        
        // Compter le nombre total d'épaisseurs NOK (rattrapées ou non)
        countNonConformingThicknesses() {
            // Compter simplement toutes les valeurs dans rattrapages
            // Car toute valeur dans rattrapages est une NOK d'origine
            return Object.keys(this.rattrapages).length;
        },
        
        // Vérifier s'il y a des épaisseurs NOK non rattrapées
        hasUnrecoveredNOK() {
            debug('Checking unrecovered NOK. Rattrapages:', this.rattrapages);
            debug('ThicknessValues:', this.thicknessValues);
            debug('Thickness spec:', this.thicknessSpec);
            
            if (!this.thicknessSpec) return false;
            
            const min = this.thicknessSpec.value_min;
            const max = this.thicknessSpec.value_max;
            
            // Les valeurs NOK sont dans rattrapages
            // Les rattrapages (corrections) sont dans thicknessValues
            for (const [key, nokValue] of Object.entries(this.rattrapages)) {
                if (nokValue) {
                    // On a une valeur NOK d'origine
                    // Vérifier si elle a été rattrapée
                    const rattrapageValue = this.thicknessValues[key];
                    
                    if (!rattrapageValue) {
                        // Pas de rattrapage du tout -> c'est OK (juste une NOK seule)
                        continue;
                    }
                    
                    // Il y a un rattrapage, vérifier s'il est aussi NOK
                    const rattrapageNum = parseFloat(rattrapageValue);
                    if (!isNaN(rattrapageNum)) {
                        if ((min !== null && rattrapageNum < min) || (max !== null && rattrapageNum > max)) {
                            debug(`Found unrecovered NOK at ${key}: original=${nokValue}, rattrapage=${rattrapageNum}`);
                            return true; // Rattrapage aussi NOK -> NON CONFORME
                        }
                    }
                }
            }
            return false;
        },
        
        // Récupérer la limite NOK depuis les types de défauts
        getNOKLimit() {
            // Chercher le défaut "Epaisseurs" dans TOUS les types (pas seulement ceux filtrés)
            if (this.allDefectTypes && this.allDefectTypes.length > 0) {
                const thicknessDefect = this.allDefectTypes.find(d => d.name === 'Epaisseurs');
                if (thicknessDefect && thicknessDefect.threshold !== undefined && thicknessDefect.threshold !== null) {
                    debug(`Found thickness defect limit: ${thicknessDefect.threshold}`);
                    return thicknessDefect.threshold;
                }
            }
            return null;
        },
        
        // Calculer le statut de conformité
        calculateConformityStatus() {
            // 1. Vérifier s'il y a des NOK non rattrapés (rattrapage NOK)
            const hasUnrecovered = this.hasUnrecoveredNOK();
            if (hasUnrecovered) {
                return 'NON_CONFORME';
            }
            
            // 2. Vérifier les défauts bloquants
            const blockingDefects = this.checkBlockingDefects();
            if (blockingDefects.hasBlocking) {
                return 'NON_CONFORME';
            }
            
            // 3. Vérifier les défauts avec seuil
            const thresholdDefects = this.checkThresholdDefects();
            if (thresholdDefects.exceeded) {
                return 'NON_CONFORME';
            }
            
            // 4. Vérifier la limite de NOK uniquement si elle est définie et > 0
            const nokLimit = this.getNOKLimit();
            
            if (nokLimit !== null && nokLimit !== undefined && nokLimit > 0) {
                const nokCount = this.countNonConformingThicknesses();
                if (nokCount >= nokLimit) {  // >= au lieu de > pour que limite 1 = non conforme à partir de 1
                    return 'NON_CONFORME';
                }
            }
            
            // 5. Vérifier le grammage (depuis la sticky bar)
            if (this.grammageStatus === 'nok') {
                return 'NON_CONFORME';
            }
            
            // Si tous les critères sont OK, on est CONFORME
            return 'CONFORME';
        },
        
        // Vérifier les défauts bloquants
        checkBlockingDefects() {
            if (!this.allDefectTypes) return { hasBlocking: false };
            
            // Parcourir tous les défauts enregistrés
            for (const cellDefects of Object.values(this.defects)) {
                for (const defectName of cellDefects) {
                    // Trouver le type de défaut correspondant
                    const defectType = this.allDefectTypes.find(d => d.name === defectName);
                    if (defectType && defectType.severity === 'blocking') {
                        return { hasBlocking: true, defectName: defectName };
                    }
                }
            }
            
            return { hasBlocking: false };
        },
        
        // Vérifier les défauts avec seuil
        checkThresholdDefects() {
            if (!this.allDefectTypes) return { exceeded: false };
            
            // Compter les occurrences de chaque type de défaut
            const defectCounts = {};
            for (const cellDefects of Object.values(this.defects)) {
                for (const defectName of cellDefects) {
                    defectCounts[defectName] = (defectCounts[defectName] || 0) + 1;
                }
            }
            
            // Vérifier les seuils
            for (const [defectName, count] of Object.entries(defectCounts)) {
                const defectType = this.allDefectTypes.find(d => d.name === defectName);
                if (defectType && defectType.severity === 'threshold' && defectType.threshold !== undefined && defectType.threshold !== null) {
                    if (count >= defectType.threshold) {
                        return { 
                            exceeded: true, 
                            defectName: defectName,
                            count: count,
                            threshold: defectType.threshold
                        };
                    }
                }
            }
            
            return { exceeded: false };
        },
        
        // Vérifier le statut du grammage depuis la sticky bar
        checkGrammageStatus() {
            // Chercher l'instance de la sticky bar
            const stickyBarElement = document.querySelector('[x-data*="stickyBar"]');
            if (stickyBarElement && stickyBarElement._x_dataStack) {
                const stickyBarInstance = stickyBarElement._x_dataStack[0];
                return stickyBarInstance.grammageStatus || '';
            }
            return '';
        },
        
        // Vérifier si toutes les épaisseurs sont remplies
        areAllThicknessesFilled() {
            // Compter le nombre de cellules d'épaisseur
            let thicknessCells = 0;
            let filledCells = 0;
            
            this.gridCells.forEach(cell => {
                if (cell.isThickness) {
                    thicknessCells++;
                    const key = this.getCellKey(cell.row, cell.col);
                    // Une cellule est remplie si :
                    // 1. Elle a une valeur dans thicknessValues (valeur normale ou correction)
                    // 2. OU elle a un rattrapage ET une correction dans thicknessValues
                    // Mais PAS si elle a seulement un rattrapage sans correction
                    if (this.thicknessValues[key]) {
                        // Il y a une valeur (normale ou correction)
                        filledCells++;
                    } else if (this.rattrapages[key]) {
                        // Il y a un rattrapage mais pas de correction
                        // Ce n'est PAS considéré comme rempli
                        // Ne pas incrémenter filledCells
                    }
                }
            });
            
            const result = thicknessCells > 0 && thicknessCells === filledCells;
            debug(`areAllThicknessesFilled: ${filledCells}/${thicknessCells} = ${result}`);
            return result;
        },
        
        // Propriété computed pour savoir si toutes les épaisseurs sont remplies
        get allThicknessesFilled() {
            return this.areAllThicknessesFilled();
        },
        
        // Propriété computed pour le statut de conformité
        get conformityStatus() {
            try {
                const status = this.calculateConformityStatus();
                const allFilled = this.areAllThicknessesFilled();
                
                // Émettre l'événement si le statut a changé ou si l'état de remplissage a changé
                if (this._lastConformityStatus !== status || this._lastAllFilled !== allFilled) {
                    const previousStatus = this._lastConformityStatus;
                    this._lastConformityStatus = status;
                    this._lastAllFilled = allFilled;
                    
                    debug(`Roll conformity changed: ${previousStatus} -> ${status}, allFilled: ${allFilled}`);
                    
                    window.eventBus.emit(window.eventBus.EVENTS.ROLL_CONFORMITY_CHANGED, { 
                        status,
                        previousStatus,
                        allThicknessesFilled: allFilled
                    });
                }
                
                return status;
            } catch (error) {
                console.error('Error calculating conformity status:', error);
                return 'CONFORME'; // Par défaut
            }
        },
        
        // Récupérer le résumé des épaisseurs NOK
        getNOKSummary() {
            const details = [];
            const count = Object.keys(this.rattrapages).length;
            
            // Parcourir les rattrapages (valeurs NOK d'origine)
            Object.entries(this.rattrapages).forEach(([key, nokValue]) => {
                if (nokValue) {
                    // Extraire row et col de la clé
                    const [row, col] = key.split('-').map(Number);
                    const meter = row + 1; // Le mètre est row + 1
                    
                    // Vérifier s'il y a un rattrapage
                    const rattrapageValue = this.thicknessValues[key];
                    
                    details.push({
                        key: key,
                        meter: meter,
                        value: nokValue,
                        rattrapage: rattrapageValue || null
                    });
                }
            });
            
            // Trier par mètre
            details.sort((a, b) => a.meter - b.meter);
            
            return {
                count: count,
                details: details
            };
        },
        
        // === Navigation clavier ===
        
        // Obtenir toutes les cellules d'épaisseur dans l'ordre
        getThicknessCells() {
            return this.gridCells.filter(cell => cell.isThickness)
                                 .sort((a, b) => a.row === b.row ? a.col - b.col : a.row - b.row);
        },
        
        // Trouver la prochaine cellule d'épaisseur vide ou field sticky bar
        findNextEmptyThicknessCell(fromRow, fromCol, reverse = false) {
            const cells = this.getThicknessCells();
            const currentIndex = cells.findIndex(cell => cell.row === fromRow && cell.col === fromCol);
            
            if (currentIndex === -1) return null;
            
            // Commencer la recherche depuis la position suivante
            for (let i = 1; i < cells.length; i++) {
                let searchIndex;
                if (reverse) {
                    searchIndex = (currentIndex - i + cells.length) % cells.length;
                } else {
                    searchIndex = (currentIndex + i) % cells.length;
                }
                
                const cell = cells[searchIndex];
                const key = this.getCellKey(cell.row, cell.col);
                
                // Vérifier si la cellule est vide
                if (!this.thicknessValues[key] || this.thicknessValues[key].trim() === '') {
                    return cell;
                }
            }
            
            // Si toutes les cellules d'épaisseur sont pleines, aller aux champs sticky bar
            // Chercher le premier champ vide dans la sticky bar
            const nextStickyField = this.findNextStickyField('', false);
            return { type: 'sticky-field', field: nextStickyField };
        },
        
        // Mettre le focus sur une cellule d'épaisseur
        focusThicknessCell(row, col) {
            this.$nextTick(() => {
                const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
                if (cell) {
                    const input = cell.querySelector('input[type="text"]');
                    if (input) {
                        input.focus();
                        input.select();
                    }
                }
            });
        },
        
        // Mettre le focus sur un champ de la sticky bar
        focusStickyField(fieldName) {
            this.$nextTick(() => {
                const stickyBarElement = document.querySelector('[x-data*="stickyBar"]');
                if (stickyBarElement) {
                    let element = null;
                    
                    // Sélecteurs pour les différents champs
                    switch (fieldName) {
                        case 'tubeMass':
                            element = stickyBarElement.querySelector('input[x-model="tubeMass"]');
                            break;
                        case 'length':
                            element = stickyBarElement.querySelector('input[x-model="length"]');
                            break;
                        case 'totalMass':
                            element = stickyBarElement.querySelector('input[x-model="totalMass"]');
                            break;
                        case 'saveButton':
                            // Chercher le bouton de sauvegarde dans la sticky bar
                            element = stickyBarElement.querySelector('button[x-text*="Sauvegarder"], button:has(span[x-text*="Sauvegarder"])');
                            if (!element) {
                                // Fallback: chercher par le texte
                                element = Array.from(stickyBarElement.querySelectorAll('button')).find(btn => 
                                    btn.textContent.includes('Sauvegarder') || btn.textContent.includes('Découpe')
                                );
                            }
                            break;
                    }
                    
                    if (element) {
                        element.focus();
                        if (element.tagName === 'INPUT') {
                            element.select();
                        }
                    }
                }
            });
        },

        // Trouver le prochain champ sticky bar vide
        findNextStickyField(currentField, reverse = false) {
            const fields = ['tubeMass', 'length', 'totalMass'];
            const stickyBarElement = document.querySelector('[x-data*="stickyBar"]');
            if (!stickyBarElement || !stickyBarElement._x_dataStack) return 'totalMass';
            
            const stickyBarData = stickyBarElement._x_dataStack[0];
            const currentIndex = fields.indexOf(currentField);
            
            // Si on vient de la grille d'épaisseurs (currentField vide), chercher le premier champ vide
            if (currentIndex === -1) {
                for (const field of fields) {
                    const value = stickyBarData[field];
                    if (!value || value.toString().trim() === '') {
                        return field;
                    }
                }
                // Si tous pleins, aller à totalMass
                return 'totalMass';
            }
            
            // Cas spécial : si on est sur totalMass et tout est rempli, aller au bouton sauvegarder
            if (currentField === 'totalMass' && !reverse) {
                // Vérifier si tous les champs sont remplis
                const allFilled = fields.every(field => {
                    const value = stickyBarData[field];
                    return value && value.toString().trim() !== '';
                });
                
                if (allFilled) {
                    return 'saveButton';
                }
            }
            
            // Chercher le prochain champ vide
            for (let i = 1; i < fields.length; i++) {
                let searchIndex;
                if (reverse) {
                    searchIndex = (currentIndex - i + fields.length) % fields.length;
                } else {
                    searchIndex = (currentIndex + i) % fields.length;
                }
                
                const field = fields[searchIndex];
                const value = stickyBarData[field];
                
                if (!value || value.toString().trim() === '') {
                    return field;
                }
            }
            
            // Si tous pleins, aller au suivant ou à totalMass
            if (reverse) {
                return currentIndex > 0 ? fields[currentIndex - 1] : fields[fields.length - 1];
            } else {
                return 'totalMass'; // Toujours totalMass si tous pleins
            }
        },

        // Navigation vers la prochaine cellule d'épaisseur ou sticky field
        navigateToNextThickness(currentRow, currentCol, reverse = false) {
            const next = this.findNextEmptyThicknessCell(currentRow, currentCol, reverse);
            if (next) {
                if (next.type === 'sticky-field') {
                    this.focusStickyField(next.field);
                } else {
                    this.focusThicknessCell(next.row, next.col);
                }
            }
        },

        // Navigation depuis le bouton save vers les contrôles qualité
        navigateFromSaveButton(reverse = false) {
            // Aller au premier champ vide des contrôles qualité
            const firstQualityField = this.findNextQualityField('', reverse);
            if (firstQualityField) {
                this.focusQualityField(firstQualityField);
            }
        },

        // Navigation depuis un champ sticky bar
        navigateFromStickyField(currentField, reverse = false) {
            const nextField = this.findNextStickyField(currentField, reverse);
            if (nextField) {
                this.focusStickyField(nextField);
            }
        },

        // Gestion spéciale pour totalMass : blur d'abord, puis navigation
        handleStickyFieldNavigation(event, currentField, reverse = false) {
            // Pour totalMass, on a besoin du blur pour les calculs
            if (currentField === 'totalMass') {
                // Laisser le blur se faire naturellement d'abord
                setTimeout(() => {
                    // Puis naviguer après le blur
                    const nextField = this.findNextStickyField(currentField, reverse);
                    if (nextField && nextField === 'saveButton') {
                        // Seulement aller au bouton save si tout est vraiment rempli
                        this.focusStickyField(nextField);
                        event.preventDefault();
                    }
                    // Sinon laisser Tab faire sa navigation normale
                }, 10);
            } else {
                // Pour les autres champs, navigation normale avec prevent
                event.preventDefault();
                this.navigateFromStickyField(currentField, reverse);
            }
        },

        // === Navigation dans les contrôles qualité ===

        // Définir l'ordre des champs de contrôle qualité
        getQualityFieldsOrder() {
            return [
                // Micronaire G (3 champs)
                'micromaireG[0]', 'micromaireG[1]', 'micromaireG[2]',
                // Micronaire D (3 champs)  
                'micromaireD[0]', 'micromaireD[1]', 'micromaireD[2]',
                // Masse Surfacique G (2 champs)
                'masseSurfaciqueGG', 'masseSurfaciqueGC',
                // Masse Surfacique D (2 champs)
                'masseSurfaciqueDC', 'masseSurfaciqueDD',
                // Extrait Sec (1 champ)
                'extraitSec'
                // Note: LOI n'est pas inclus car non sélectionnable
            ];
        },

        // Trouver le prochain champ de contrôle qualité vide
        findNextQualityField(currentField, reverse = false) {
            const fields = this.getQualityFieldsOrder();
            const qualityElement = document.querySelector('[x-data*="qualityControl"]');
            if (!qualityElement || !qualityElement._x_dataStack) return null;

            const qualityData = qualityElement._x_dataStack[0];
            const currentIndex = fields.indexOf(currentField);

            // Si on vient d'ailleurs (currentField vide ou non trouvé), chercher le premier champ vide
            if (currentIndex === -1) {
                for (const field of fields) {
                    const value = this.getQualityFieldValue(qualityData, field);
                    if (!value || value.toString().trim() === '') {
                        return field;
                    }
                }
                return null; // Tous pleins
            }

            // Chercher le prochain champ vide
            for (let i = 1; i < fields.length; i++) {
                let searchIndex;
                if (reverse) {
                    searchIndex = (currentIndex - i + fields.length) % fields.length;
                } else {
                    searchIndex = (currentIndex + i) % fields.length;
                }

                const field = fields[searchIndex];
                const value = this.getQualityFieldValue(qualityData, field);

                if (!value || value.toString().trim() === '') {
                    return field;
                }
            }

            // Si tous pleins, navigation séquentielle
            if (reverse) {
                return currentIndex > 0 ? fields[currentIndex - 1] : fields[fields.length - 1];
            } else {
                return currentIndex < fields.length - 1 ? fields[currentIndex + 1] : null;
            }
        },

        // Helper pour récupérer la valeur d'un champ de contrôle qualité
        getQualityFieldValue(qualityData, fieldName) {
            if (fieldName.includes('[')) {
                // Cas des tableaux comme micromaireG[0]
                const [baseName, indexStr] = fieldName.split(/[\[\]]/);
                const index = parseInt(indexStr);
                return qualityData[baseName] ? qualityData[baseName][index] : '';
            } else {
                // Cas des champs simples
                return qualityData[fieldName] || '';
            }
        },

        // Mettre le focus sur un champ de contrôle qualité
        focusQualityField(fieldName) {
            this.$nextTick(() => {
                let input = null;

                if (fieldName.includes('[')) {
                    // Cas des tableaux comme micromaireG[0]
                    const [baseName, indexStr] = fieldName.split(/[\[\]]/);
                    input = document.querySelector(`input[x-model="${baseName}[${indexStr}]"]`);
                } else {
                    // Cas des champs simples
                    input = document.querySelector(`input[x-model="${fieldName}"]`);
                }

                if (input) {
                    input.focus();
                    input.select();
                }
            });
        },

        // Navigation dans les contrôles qualité
        navigateInQualityFields(currentField, reverse = false) {
            const nextField = this.findNextQualityField(currentField, reverse);
            if (nextField) {
                this.focusQualityField(nextField);
            }
        },
        
        
    };
}

// Export global pour Alpine
window.rollGrid = rollGrid;