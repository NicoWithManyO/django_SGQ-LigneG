/**
 * Composant Shift Form V2
 * Gère le formulaire de poste avec génération automatique de l'ID
 */
class ShiftFormV2 {
    constructor() {
        this.container = null;
        this.operatorSelect = null;
        this.dateInput = null;
        this.vacationSelect = null;
        this.shiftIdDisplay = null;
        
        this.init();
    }
    
    async init() {
        // Setup direct car on attend déjà que tout soit prêt avant de créer l'instance
        this.setup();
    }
    
    async setup() {
        this.container = document.getElementById('shift-form-container');
        if (!this.container) {
            console.error('❌ ShiftFormV2: Container not found!');
            return;
        }
        
        // Récupérer les éléments du formulaire
        this.operatorSelect = document.getElementById('operator-select');
        this.dateInput = document.getElementById('shift-date');
        this.vacationSelect = document.getElementById('vacation');
        this.shiftIdDisplay = document.getElementById('shift-id-display');
        
        console.log('📋 ShiftFormV2 elements:', {
            operatorSelect: !!this.operatorSelect,
            dateInput: !!this.dateInput,
            vacationSelect: !!this.vacationSelect,
            shiftIdDisplay: !!this.shiftIdDisplay
        });
        
        // S'abonner aux changements d'état
        this.subscribeToState();
        
        // Attacher les event listeners
        this.attachEventListeners();
        
        // Charger l'état initial
        await this.loadInitialState();
    }
    
    subscribeToState() {
        if (!window.stateManager) return;
        
        // S'abonner aux changements du shift
        window.stateManager.subscribe('shift.operatorId', ({ newValue }) => {
            if (this.operatorSelect && this.operatorSelect.value !== newValue) {
                this.operatorSelect.value = newValue || '';
            }
        });
        
        window.stateManager.subscribe('shift.date', ({ newValue }) => {
            if (this.dateInput && this.dateInput.value !== newValue) {
                this.dateInput.value = newValue || '';
            }
        });
        
        window.stateManager.subscribe('shift.vacation', ({ newValue }) => {
            console.log('📌 Vacation state changed:', newValue, 'Current DOM value:', this.vacationSelect?.value);
            if (this.vacationSelect && this.vacationSelect.value !== newValue) {
                this.vacationSelect.value = newValue || '';
                console.log('✅ Updated vacation select to:', this.vacationSelect.value);
            }
        });
        
        window.stateManager.subscribe('shift.shiftId', ({ newValue }) => {
            if (this.shiftIdDisplay) {
                this.shiftIdDisplay.textContent = newValue || '--';
                // Changer la couleur quand l'ID est généré
                if (newValue) {
                    this.shiftIdDisplay.classList.remove('text-muted');
                    this.shiftIdDisplay.classList.add('text-primary', 'fw-bold');
                } else {
                    this.shiftIdDisplay.classList.add('text-muted');
                    this.shiftIdDisplay.classList.remove('text-primary', 'fw-bold');
                }
            }
        });
    }
    
    attachEventListeners() {
        // Opérateur
        if (this.operatorSelect) {
            this.operatorSelect.addEventListener('change', async (e) => {
                const operatorId = e.target.value;
                
                if (window.commandBus) {
                    await window.commandBus.execute('CHANGE_OPERATOR', { operatorId });
                }
                
                // Générer l'ID si tous les champs sont remplis
                this.generateShiftId();
            });
        }
        
        // Date
        if (this.dateInput) {
            this.dateInput.addEventListener('change', async (e) => {
                const date = e.target.value;
                
                if (window.commandBus) {
                    await window.commandBus.execute('CHANGE_SHIFT_DATE', { date });
                }
                
                // Générer l'ID si tous les champs sont remplis
                this.generateShiftId();
            });
        }
        
        // Vacation
        if (this.vacationSelect) {
            this.vacationSelect.addEventListener('change', async (e) => {
                const vacation = e.target.value;
                
                if (window.commandBus) {
                    await window.commandBus.execute('CHANGE_VACATION', { vacation });
                }
                
                // Générer l'ID si tous les champs sont remplis
                this.generateShiftId();
            });
        }
    }
    
    generateShiftId() {
        const operatorId = this.operatorSelect?.value;
        const date = this.dateInput?.value;
        const vacation = this.vacationSelect?.value;
        
        // Vérifier que tous les champs sont remplis
        if (!operatorId || !date || !vacation) {
            return;
        }
        
        // Formater la date en JJMMAA
        const dateObj = new Date(date);
        const day = String(dateObj.getDate()).padStart(2, '0');
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const year = String(dateObj.getFullYear()).slice(-2);
        const dateFormatted = `${day}${month}${year}`;
        
        // Trouver l'opérateur pour avoir son nom complet
        const operator = window.operatorsData?.find(op => op.employee_id === operatorId);
        if (!operator) return;
        
        // Extraire prénom et nom
        // Format attendu : "PrenomNOM" -> "Prenom" et "NOM"
        const match = operator.name.match(/^([A-Z][a-z]+)([A-Z]+)$/);
        let formattedName;
        
        if (match) {
            const prenom = match[1];
            const nom = match[2];
            // Capitaliser correctement : Prenom + Nom avec première lettre en majuscule
            formattedName = prenom + nom.charAt(0).toUpperCase() + nom.slice(1).toLowerCase();
        } else {
            // Fallback si le format n'est pas reconnu
            formattedName = operator.name;
        }
        
        // Générer l'ID du poste
        const shiftId = `${dateFormatted}_${formattedName}_${vacation}`;
        
        // Mettre à jour via une commande
        if (window.commandBus) {
            window.commandBus.execute('SET_SHIFT_ID', { shiftId });
        }
    }
    
    async loadInitialState() {
        if (!window.stateManager) return;
        
        const state = window.stateManager.getState('shift') || {};
        
        // Charger les valeurs initiales
        if (this.operatorSelect && state.operatorId) {
            this.operatorSelect.value = state.operatorId;
        }
        
        if (this.dateInput && state.date) {
            this.dateInput.value = state.date;
        }
        
        if (this.vacationSelect && state.vacation) {
            this.vacationSelect.value = state.vacation;
        }
        
        // Si tous les champs sont déjà remplis, générer l'ID
        if (state.operatorId && state.date && state.vacation && !state.shiftId) {
            this.generateShiftId();
        }
    }
}

// Attendre que TOUT soit prêt avant d'initialiser
document.addEventListener('DOMContentLoaded', () => {
    // Attendre un peu pour être sûr que tout est chargé
    setTimeout(() => {
        if (!window.shiftFormV2 && window.stateManager && window.commandBus) {
            window.shiftFormV2 = new ShiftFormV2();
            console.log('✅ ShiftFormV2 initialized');
        }
    }, 500);
});