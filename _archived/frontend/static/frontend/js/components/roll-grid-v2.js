/**
 * Composant RollGrid V2
 * Gestion de la grille du rouleau selon le pattern V2
 */
class RollGridComponent {
    constructor() {
        this.container = null;
        this.targetLength = 30; // Valeur par défaut
        this.defectTypes = [];
        
        // Initialiser
        this.init();
    }
    
    // Fonction pour remplir toutes les épaisseurs avec des valeurs aléatoires
    async fillRandomThickness() {
        console.log('🎲 Remplissage aléatoire des épaisseurs...');
        
        const rows = Math.min(this.targetLength, 50);
        
        for (let row = 1; row <= rows; row++) {
            // Seulement sur les lignes de mesure
            if (!this.isMeasurementRow(row)) continue;
            
            for (let col = 1; col <= 7; col++) {
                if (col === 4) continue; // Pas la colonne du milieu
                
                // Générer une valeur aléatoire entre 3 et 9
                const randomValue = (Math.random() * (9 - 3) + 3).toFixed(2);
                
                // Utiliser ADD_THICKNESS_MEASUREMENT comme dans le blur
                if (window.commandBus) {
                    await window.commandBus.execute('ADD_THICKNESS_MEASUREMENT', {
                        row: row,
                        col: col,
                        value: parseFloat(randomValue)
                    });
                }
                
                // Mettre à jour l'affichage
                const input = document.getElementById(`thickness-${row}-${col}`);
                if (input) {
                    input.value = randomValue;
                    input.classList.add('v2-input-filled');
                }
            }
        }
        
        console.log('✅ Remplissage aléatoire terminé');
    }
    
    // Fonction pour supprimer toutes les épaisseurs
    async clearAllThickness() {
        console.log('🗑️ Suppression de toutes les épaisseurs...');
        
        const rows = Math.min(this.targetLength, 50);
        
        for (let row = 1; row <= rows; row++) {
            // Seulement sur les lignes de mesure
            if (!this.isMeasurementRow(row)) continue;
            
            for (let col = 1; col <= 7; col++) {
                if (col === 4) continue; // Pas la colonne du milieu
                
                // Exécuter la commande pour supprimer la mesure (en passant null)
                if (window.commandBus) {
                    await window.commandBus.execute('ADD_THICKNESS_MEASUREMENT', {
                        row: row,
                        col: col,
                        value: null
                    });
                }
                
                // Vider l'affichage
                const input = document.getElementById(`thickness-${row}-${col}`);
                if (input) {
                    input.value = '';
                    input.classList.remove('v2-input-filled');
                }
            }
        }
        
        console.log('✅ Suppression terminée');
    }
    
    async init() {
        // Attendre que le système soit prêt
        if (window.eventBus) {
            window.eventBus.on('system:ready', () => {
                this.setup();
            });
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                this.setup();
            });
        }
    }
    
    async setup() {
        this.container = document.getElementById('roll-grid-container');
        if (!this.container) {
            console.error('Roll grid container not found');
            return;
        }
        
        // Charger les types de défauts
        await this.loadDefectTypes();
        
        // S'abonner aux changements d'état
        this.subscribeToState();
        
        // Charger l'état initial ET faire le render
        this.loadInitialState();
        
        // Render initial après avoir chargé l'état
        console.log('Setup - targetLength:', this.targetLength);
        this.render();
        
        // S'abonner à l'événement de restauration des épaisseurs
        if (window.eventBus) {
            window.eventBus.on('rollgrid:restore-thicknesses', (data) => {
                if (data && data.thicknesses) {
                    Object.entries(data.thicknesses).forEach(([key, value]) => {
                        const [row, col] = key.split('-');
                        this.updateThicknessDisplay(row, col, value);
                    });
                }
            });
            
            // S'abonner aussi à l'événement state:loaded pour recharger après que l'état soit chargé
            window.eventBus.on('state:loaded', () => {
                console.log('📊 État chargé dans roll-grid');
                console.log('📊 of.targetLength:', window.stateManager.getState('of.targetLength'));
                
                // Recharger l'état initial
                this.loadInitialState();
                
                // Faire le render si on a une longueur cible
                if (this.targetLength) {
                    console.log('✅ Render avec targetLength:', this.targetLength);
                    this.render();
                } else {
                    console.log('⚠️ Pas de targetLength après state:loaded');
                }
        }
    }
    
    async loadDefectTypes() {
        try {
            // Utiliser l'API V2 si disponible
            if (window.apiV2 && window.apiV2.getDefectTypes) {
                this.defectTypes = await window.apiV2.getDefectTypes();
                // Filtrer uniquement les types actifs
                this.defectTypes = this.defectTypes.filter(d => d.is_active !== false);
                console.log('✅ Defect types loaded from API V2:', this.defectTypes);
            } else {
                // Sinon utiliser l'endpoint direct
                const response = await fetch('/api/defect-types/');
                if (response.ok) {
                    const data = await response.json();
                    // Filtrer uniquement les types actifs
                    this.defectTypes = data.filter(d => d.is_active !== false);
                    console.log('✅ Defect types loaded from API:', this.defectTypes);
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
        } catch (error) {
            console.error('Failed to load defect types:', error);
            // Utiliser les défauts par défaut
            this.defectTypes = [
                { id: 1, name: 'Autre', severity: 'non_blocking' },
                { id: 2, name: 'Epaisseurs', severity: 'threshold', threshold_value: 3 },
                { id: 3, name: 'Infibré', severity: 'threshold', threshold_value: 3 },
                { id: 4, name: 'Insectes', severity: 'blocking' },
                { id: 5, name: 'Marque Tapis', severity: 'blocking' },
                { id: 6, name: 'Shot', severity: 'threshold', threshold_value: 3 },
                { id: 7, name: 'Trou', severity: 'blocking' }
            ];
            console.warn('Using default defect types');
        }
    }
    
    subscribeToState() {
        if (!window.stateManager) return;
        
        // S'abonner aux changements de longueur cible
        window.stateManager.subscribe('of.targetLength', (value) => {
            console.log('🎯 Changement longueur cible:', value);
            this.targetLength = value || 30;
            this.render();
        });
        
        // S'abonner aux changements d'épaisseurs depuis production.currentRoll.thicknesses
        window.stateManager.subscribe('production.currentRoll.thicknesses', (thicknesses) => {
            // Recharger toutes les épaisseurs
            Object.entries(thicknesses || {}).forEach(([key, value]) => {
                const [row, col] = key.split('-');
                this.updateThicknessDisplay(row, col, value);
            });
        });
        
        // S'abonner aux changements de défauts depuis production.currentRoll.defects
        window.stateManager.subscribe('production.currentRoll.defects', (defects) => {
            // Effacer tous les défauts actuels
            this.container.querySelectorAll('.defect-indicator').forEach(indicator => {
                indicator.remove();
            });
            
            // Afficher tous les défauts
            Object.entries(defects || {}).forEach(([key, defect]) => {
                const [row, col] = key.split('-');
                this.updateDefectDisplay(row, col, defect);
            });
        });
    }
    
    loadInitialState() {
        if (!window.stateManager) return;
        
        // Charger la longueur cible
        const targetLength = window.stateManager.getState('of.targetLength');
        if (targetLength) {
            this.targetLength = targetLength;
        } else {
            this.targetLength = 30; // Valeur par défaut
        }
        
        // Charger les épaisseurs depuis production.currentRoll.thicknesses
        const thicknesses = window.stateManager.getState('production.currentRoll.thicknesses') || {};
        
        Object.entries(thicknesses).forEach(([key, value]) => {
            const [row, col] = key.split('-');
            this.updateThicknessDisplay(row, col, value);
        });
        
        // Charger les défauts existants depuis production.currentRoll.defects
        const defects = window.stateManager.getState('production.currentRoll.defects') || {};
        Object.entries(defects).forEach(([key, defect]) => {
            const [row, col] = key.split('-');
            this.updateDefectDisplay(row, col, defect);
        });
    }
    
    render() {
        if (!this.container) return;
        
        // Sauvegarder les données actuelles avant de recréer la grille
        const currentThicknesses = window.stateManager ? window.stateManager.getState('production.currentRoll.thicknesses', {}) : {};
        const currentDefects = window.stateManager ? window.stateManager.getState('production.currentRoll.defects', {}) : {};
        
        // Nettoyer le conteneur
        this.container.innerHTML = '';
        
        // Créer la grille
        const grid = document.createElement('div');
        grid.className = 'roll-grid';
        
        // Générer les lignes
        const rows = Math.min(this.targetLength, 50);
        
        for (let row = 1; row <= rows; row++) {
            for (let col = 1; col <= 7; col++) {
                const cell = this.createCell(row, col);
                grid.appendChild(cell);
            }
        }
        
        this.container.appendChild(grid);
        
        // Restaurer les données après le rendu
        setTimeout(() => {
            // Restaurer les épaisseurs
            Object.entries(currentThicknesses).forEach(([key, value]) => {
                const [row, col] = key.split('-');
                const input = document.getElementById(`thickness-${row}-${col}`);
                if (input) {
                    input.value = value;
                    input.classList.add('v2-input-filled');
                }
            });
            
            // Restaurer les défauts
            Object.entries(currentDefects).forEach(([key, defect]) => {
                const [row, col] = key.split('-');
                if (defect) {
                    this.updateDefectDisplay(row, col, defect);
                }
            });
        }, 10);
    }
    
    createCell(row, col) {
        const cell = document.createElement('div');
        cell.className = 'roll-cell';
        cell.dataset.row = row;
        cell.dataset.col = col;
        
        // Colonne du milieu pour le métrage
        if (col === 4) {
            cell.classList.add('roll-cell-length', 'text-secondary');
            cell.textContent = `${row}`;
            return cell;
        }
        
        // Lignes de mesure
        if (this.isMeasurementRow(row)) {
            cell.classList.add('roll-cell-measurement');
            
            const input = document.createElement('input');
            input.type = 'number';
            input.step = '0.01';
            input.min = '0';
            input.className = 'thickness-input';
            input.placeholder = '-';
            input.dataset.row = row;
            input.dataset.col = col;
            input.id = `thickness-${row}-${col}`;
            
            // Event listeners selon le pattern V2
            input.addEventListener('focus', (e) => {
                e.target.select();
            });
            
            input.addEventListener('input', (e) => {
                // Juste le feedback visuel
                if (e.target.value) {
                    e.target.classList.add('v2-input-filled');
                } else {
                    e.target.classList.remove('v2-input-filled');
                }
            });
            
            input.addEventListener('blur', async (e) => {
                const value = e.target.value.trim();
                const row = parseInt(e.target.dataset.row);
                const col = parseInt(e.target.dataset.col);
                
                // Utiliser la commande pour persister
                if (window.commandBus) {
                    await window.commandBus.execute('ADD_THICKNESS_MEASUREMENT', {
                        row: row,
                        col: col,
                        value: value === '' ? null : parseFloat(value)
                    });
                }
            });
            
            // Configurer la validation numérique et la persistence
            if (window.setupThicknessField) {
                window.setupThicknessField(input);
            }
            
            cell.appendChild(input);
        }
        
        // Bouton défaut pour toutes les cellules sauf métrage
        const defectBtn = this.createDefectButton(row, col);
        cell.appendChild(defectBtn);
        
        // Container pour les badges de défauts
        const defectBadges = document.createElement('div');
        defectBadges.className = 'defect-badges';
        defectBadges.id = `defects-${row}-${col}`;
        cell.appendChild(defectBadges);
        
        return cell;
    }
    
    createDefectButton(row, col) {
        const button = document.createElement('button');
        button.className = 'defect-btn';
        button.innerHTML = '+';
        button.dataset.row = row;
        button.dataset.col = col;
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            this.openDefectMenu(e, row, col);
        });
        
        return button;
    }
    
    openDefectMenu(event, row, col) {
        // Fermer tout menu existant
        this.closeDefectMenu();
        
        // Marquer le bouton comme actif
        event.target.classList.add('defect-btn-active');
        
        // Créer le menu
        const menu = document.createElement('div');
        menu.className = 'defect-menu';
        menu.id = 'defect-menu';
        
        // Créer les items du menu
        this.defectTypes.forEach(defect => {
            // Ignorer le défaut "Epaisseurs" dans le sélecteur
            if (defect.name === 'Epaisseurs') {
                return;
            }
            
            const item = document.createElement('div');
            item.className = 'defect-menu-item';
            item.setAttribute('data-severity', defect.severity);
            
            // Créer une abréviation depuis le nom
            const abbr = this.getDefectAbbreviation(defect.name);
            item.innerHTML = `<span class="defect-code">${abbr}</span> ${defect.name}`;
            
            item.addEventListener('click', async () => {
                // Exécuter la commande
                if (window.commandBus) {
                    await window.commandBus.execute('ADD_DEFECT', {
                        row: parseInt(row),
                        col: parseInt(col),
                        defectId: defect.id,
                        defectName: defect.name,
                        severity: defect.severity
                    });
                }
                this.closeDefectMenu();
            });
            
            menu.appendChild(item);
        });
        
        // Positionner le menu
        const btnRect = event.target.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${btnRect.bottom + 5}px`;
        menu.style.left = `${btnRect.left - 150}px`;
        
        document.body.appendChild(menu);
        
        // Fermer au clic ailleurs
        setTimeout(() => {
            document.addEventListener('click', this.closeDefectMenu);
        }, 0);
    }
    
    closeDefectMenu() {
        const menu = document.getElementById('defect-menu');
        if (menu) {
            menu.remove();
            document.removeEventListener('click', this.closeDefectMenu);
        }
        
        // Retirer la classe active
        document.querySelectorAll('.defect-btn-active').forEach(btn => {
            btn.classList.remove('defect-btn-active');
        });
    }
    
    updateThicknessDisplay(row, col, value) {
        const input = document.getElementById(`thickness-${row}-${col}`);
        if (input && value !== undefined) {
            input.value = value || '';
            if (value) {
                input.classList.add('v2-input-filled');
            } else {
                input.classList.remove('v2-input-filled');
            }
        }
    }
    
    updateDefectDisplay(row, col, defectData = null) {
        const cell = this.container.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (!cell) return;
        
        // Retirer l'indicateur existant s'il y en a un
        const existingIndicator = cell.querySelector('.defect-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Si pas de données de défaut, chercher dans l'état
        if (!defectData) {
            const defects = window.stateManager.getState('production.currentRoll.defects') || {};
            defectData = defects[`${row}-${col}`];
        }
        
        // Si on a un défaut, afficher l'indicateur
        if (defectData) {
            const indicator = document.createElement('div');
            indicator.className = 'defect-indicator';
            
            // Trouver l'abréviation du défaut
            const defectType = this.defectTypes.find(d => d.id === defectData.id);
            const abbr = defectType ? this.getDefectAbbreviation(defectType.name) : '?';
            
            indicator.textContent = abbr;
            indicator.title = defectData.name;
            
            // Appliquer la classe de sévérité
            if (defectData.severity === 'blocking') {
                indicator.classList.add('defect-blocking');
            } else if (defectData.severity === 'major') {
                indicator.classList.add('defect-major');
            }
            
            // Ajouter l'indicateur à la cellule
            cell.appendChild(indicator);
        }
    }
    
    getDefectAbbreviation(name) {
        // Créer des abréviations cohérentes
        const abbreviations = {
            'Autre': 'AUT',
            'Epaisseurs': 'EP',
            'Infibré': 'INF',
            'Insectes': 'INS',
            'Marque Tapis': 'MT',
            'Shot': 'SH',
            'Trou': 'TR'
        };
        
        return abbreviations[name] || name.substring(0, 3).toUpperCase();
    }
    
    isMeasurementRow(row) {
        // Mesure à 3m, puis tous les 5m
        return row === 3 || (row > 3 && (row - 3) % 5 === 0);
    }
}

// Créer l'instance globale
const rollGridComponent = new RollGridComponent();
window.rollGridComponent = rollGridComponent;