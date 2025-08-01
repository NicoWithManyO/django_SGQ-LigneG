/**
 * Composant V2 pour la gestion de l'enroulement
 * Affiche les compteurs, métrages et statistiques
 */

class WindingManager {
    constructor() {
        this.elements = {};
        this.init();
    }
    
    init() {
        // Attendre que le système soit prêt
        if (window.eventBus) {
            window.eventBus.on('system:ready', () => {
                this.setupEventListeners();
                this.initializeUI();
            });
        } else {
            // Fallback
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => {
                    this.setupEventListeners();
                    this.initializeUI();
                }, 500);
            });
        }
    }
    
    setupEventListeners() {
        // S'abonner aux événements
        if (window.eventBus) {
            window.eventBus.on('winding:length-updated', this.handleLengthUpdate.bind(this));
            window.eventBus.on('winding:counters-reset', this.handleCountersReset.bind(this));
            window.eventBus.on('winding:roll-added', this.handleRollAdded.bind(this));
            window.eventBus.on('winding:target-updated', this.handleTargetUpdate.bind(this));
        }
        
        // S'abonner aux changements d'état
        if (window.stateManager) {
            window.stateManager.subscribe('winding.currentLength', this.updateCurrentLength.bind(this));
            window.stateManager.subscribe('winding.okLength', this.updateConformityDisplay.bind(this));
            window.stateManager.subscribe('winding.nokLength', this.updateConformityDisplay.bind(this));
            window.stateManager.subscribe('winding.progress', this.updateProgressBar.bind(this));
        }
    }
    
    /**
     * Initialiser l'interface utilisateur
     */
    initializeUI() {
        // Créer le conteneur principal si nécessaire
        let container = document.getElementById('winding-display');
        if (!container) {
            // Si pas de conteneur spécifique, créer dans la sticky bar
            const stickyBar = document.getElementById('sticky-bar-container');
            if (stickyBar) {
                container = this.createWindingDisplay();
                const content = stickyBar.querySelector('[style*="max-width: 1400px"]');
                if (content) {
                    const centerDiv = content.querySelector('[style*="flex: 1"]');
                    if (centerDiv) {
                        centerDiv.innerHTML = '';
                        centerDiv.appendChild(container);
                    }
                }
            }
        }
        
        // Stocker les références aux éléments
        this.elements = {
            currentLength: container?.querySelector('.winding-current-length'),
            totalLength: container?.querySelector('.winding-total-length'),
            okLength: container?.querySelector('.winding-ok-length'),
            nokLength: container?.querySelector('.winding-nok-length'),
            conformityRatio: container?.querySelector('.winding-conformity-ratio'),
            progressBar: container?.querySelector('.winding-progress-bar'),
            progressText: container?.querySelector('.winding-progress-text'),
            averageSpeed: container?.querySelector('.winding-average-speed')
        };
        
        // Charger les valeurs initiales
        this.loadInitialValues();
    }
    
    /**
     * Créer l'affichage de l'enroulement
     */
    createWindingDisplay() {
        const display = document.createElement('div');
        display.id = 'winding-display';
        display.className = 'winding-display-v2';
        display.innerHTML = `
            <div class="d-flex align-items-center gap-4">
                <!-- Métrage actuel -->
                <div class="winding-metric">
                    <div class="winding-metric-label">Métrage</div>
                    <div class="winding-metric-value">
                        <span class="winding-current-length">0</span> m
                    </div>
                </div>
                
                <!-- Séparateur -->
                <div class="winding-separator"></div>
                
                <!-- Compteurs OK/NOK -->
                <div class="winding-conformity">
                    <div class="d-flex gap-3">
                        <div class="winding-ok">
                            <i class="bi bi-check-circle-fill text-success"></i>
                            <span class="winding-ok-length">0</span> m
                        </div>
                        <div class="winding-nok">
                            <i class="bi bi-x-circle-fill text-danger"></i>
                            <span class="winding-nok-length">0</span> m
                        </div>
                    </div>
                    <div class="winding-conformity-ratio-container">
                        <small class="text-muted">Conformité: <span class="winding-conformity-ratio">100</span>%</small>
                    </div>
                </div>
                
                <!-- Séparateur -->
                <div class="winding-separator"></div>
                
                <!-- Progression -->
                <div class="winding-progress" style="min-width: 200px;">
                    <div class="winding-progress-label">
                        <span>Progression</span>
                        <span class="winding-progress-text">0 / 0 m</span>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar winding-progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
                
                <!-- Vitesse moyenne -->
                <div class="winding-speed">
                    <div class="winding-metric-label">Vitesse</div>
                    <div class="winding-metric-value">
                        <span class="winding-average-speed">0</span> m/min
                    </div>
                </div>
            </div>
        `;
        
        // Ajouter les styles CSS
        this.injectStyles();
        
        return display;
    }
    
    /**
     * Injecter les styles CSS
     */
    injectStyles() {
        if (document.getElementById('winding-v2-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'winding-v2-styles';
        style.textContent = `
            .winding-display-v2 {
                padding: 0.5rem 0;
            }
            
            .winding-metric {
                text-align: center;
            }
            
            .winding-metric-label {
                font-size: 0.75rem;
                color: var(--v2-gray-600);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.25rem;
            }
            
            .winding-metric-value {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--v2-primary);
            }
            
            .winding-separator {
                width: 1px;
                height: 40px;
                background: var(--v2-gray-300);
            }
            
            .winding-conformity {
                text-align: center;
            }
            
            .winding-ok, .winding-nok {
                font-size: 1.125rem;
                font-weight: 500;
            }
            
            .winding-conformity-ratio-container {
                margin-top: 0.25rem;
            }
            
            .winding-progress-label {
                display: flex;
                justify-content: space-between;
                font-size: 0.875rem;
                margin-bottom: 0.25rem;
            }
            
            .winding-speed {
                text-align: center;
                min-width: 100px;
            }
            
            .v2-icon-animate {
                animation: v2-pulse 0.3s ease-in-out;
            }
            
            @keyframes v2-pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Charger les valeurs initiales depuis le StateManager
     */
    async loadInitialValues() {
        if (!window.stateManager) return;
        
        // Charger toutes les valeurs
        const currentLength = window.stateManager.getState('winding.currentLength', 0);
        const okLength = window.stateManager.getState('winding.okLength', 0);
        const nokLength = window.stateManager.getState('winding.nokLength', 0);
        const targetLength = window.stateManager.getState('winding.targetLength', 0);
        const averageSpeed = window.stateManager.getState('winding.stats.averageSpeed', 0);
        
        // Mettre à jour l'affichage
        this.updateDisplay({
            currentLength,
            okLength,
            nokLength,
            targetLength,
            averageSpeed
        });
        
        // Calculer les statistiques
        if (window.commandBus) {
            await window.commandBus.execute('CALCULATE_WINDING_STATS');
        }
    }
    
    /**
     * Mettre à jour l'affichage complet
     */
    updateDisplay(data) {
        if (this.elements.currentLength && data.currentLength !== undefined) {
            this.elements.currentLength.textContent = Math.round(data.currentLength);
        }
        
        if (this.elements.okLength && data.okLength !== undefined) {
            this.elements.okLength.textContent = Math.round(data.okLength);
        }
        
        if (this.elements.nokLength && data.nokLength !== undefined) {
            this.elements.nokLength.textContent = Math.round(data.nokLength);
        }
        
        if (this.elements.averageSpeed && data.averageSpeed !== undefined) {
            this.elements.averageSpeed.textContent = data.averageSpeed;
        }
        
        // Calculer et afficher le ratio de conformité
        if (data.okLength !== undefined && data.nokLength !== undefined) {
            const total = data.okLength + data.nokLength;
            const ratio = total > 0 ? (data.okLength / total) * 100 : 100;
            if (this.elements.conformityRatio) {
                this.elements.conformityRatio.textContent = ratio.toFixed(1);
            }
        }
        
        // Mettre à jour la progression
        if (data.currentLength !== undefined && data.targetLength !== undefined) {
            const progress = data.targetLength > 0 ? (data.currentLength / data.targetLength) * 100 : 0;
            if (this.elements.progressBar) {
                this.elements.progressBar.style.width = `${Math.min(100, progress)}%`;
            }
            if (this.elements.progressText) {
                this.elements.progressText.textContent = `${Math.round(data.currentLength)} / ${Math.round(data.targetLength)} m`;
            }
        }
    }
    
    /**
     * Gérer la mise à jour de longueur
     */
    handleLengthUpdate(data) {
        this.updateDisplay({
            currentLength: data.length,
            totalLength: data.totalLength
        });
        
        // Animation sur le chiffre
        if (this.elements.currentLength) {
            this.elements.currentLength.classList.add('v2-icon-animate');
            setTimeout(() => {
                this.elements.currentLength.classList.remove('v2-icon-animate');
            }, 300);
        }
    }
    
    /**
     * Gérer la réinitialisation des compteurs
     */
    handleCountersReset() {
        this.updateDisplay({
            currentLength: 0,
            okLength: 0,
            nokLength: 0,
            totalLength: 0
        });
    }
    
    /**
     * Gérer l'ajout d'un rouleau
     */
    handleRollAdded(data) {
        // Les compteurs sont déjà mis à jour par les subscriptions
        // On peut ajouter une animation ou notification ici si nécessaire
    }
    
    /**
     * Gérer la mise à jour de la cible
     */
    handleTargetUpdate(data) {
        this.updateDisplay({
            targetLength: data.targetLength,
            currentLength: data.currentLength
        });
    }
    
    /**
     * Mettre à jour l'affichage de la longueur actuelle
     */
    updateCurrentLength(data) {
        if (this.elements.currentLength) {
            this.elements.currentLength.textContent = Math.round(data.newValue || 0);
        }
    }
    
    /**
     * Mettre à jour l'affichage de conformité
     */
    updateConformityDisplay() {
        if (!window.stateManager) return;
        
        const okLength = window.stateManager.getState('winding.okLength', 0);
        const nokLength = window.stateManager.getState('winding.nokLength', 0);
        
        this.updateDisplay({ okLength, nokLength });
    }
    
    /**
     * Mettre à jour la barre de progression
     */
    updateProgressBar(data) {
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = `${Math.min(100, data.newValue || 0)}%`;
        }
    }
}

// Créer et exposer l'instance globale
window.windingManager = new WindingManager();