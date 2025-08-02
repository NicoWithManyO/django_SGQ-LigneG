/**
 * Composant Alpine.js : Barre Sticky
 * Affiche les informations en temps réel et actions globales
 */

function stickyBar() {
    return {
        // État local
        currentDateTime: '',
        rollId: '',
        ofStatus: '',
        rollNumber: '001',
        ofNumber: '',
        shiftId: '',
        rollSaved: false,
        shiftSaved: false,
        rollStatus: '', // '', 'ok', 'nok'
        
        // Données du rouleau
        tubeMass: '',
        length: '',
        totalMass: '',
        netMass: '',
        grammage: '',
        nextTubeMass: '',
        
        // Timer pour l'horloge
        clockTimer: null,
        
        // Initialisation
        init() {
            debug('Sticky bar initialized');
            
            // Démarrer l'horloge
            this.updateClock();
            this.clockTimer = setInterval(() => this.updateClock(), 1000);
            
            // Charger les données initiales depuis la session
            this.loadFromSession();
            
            // Écouter les changements globaux
            this.listenToGlobalEvents();
            
            // Watchers pour auto-save
            this.$watch('rollNumber', () => this.handleRollNumberChange());
            this.$watch('tubeMass', () => this.handleDataChange());
            this.$watch('length', () => this.handleDataChange());
            this.$watch('totalMass', () => this.handleDataChange());
            this.$watch('nextTubeMass', () => this.handleDataChange());
            
            // Cleanup se fera automatiquement quand le composant est détruit
        },
        
        // Charger depuis la session
        loadFromSession() {
            const ofData = window.sessionData?.of || {};
            const rollData = window.sessionData?.roll || {};
            const shiftData = window.sessionData?.shift || {};
            
            this.ofNumber = ofData.ofEnCours || '';
            this.rollNumber = window.sessionData?.sticky_roll_number || rollData.rollNumber || '001';
            this.shiftId = shiftData.shiftId || '';
            
            // Charger les données du rouleau
            this.tubeMass = window.sessionData?.sticky_tube_mass || '';
            this.length = window.sessionData?.sticky_length || '';
            this.totalMass = window.sessionData?.sticky_total_mass || '';
            this.nextTubeMass = window.sessionData?.sticky_next_tube_mass || '';
            
            this.updateRollId();
            this.updateOFStatus();
            this.calculateValues();
        },
        
        // Mettre à jour l'horloge
        updateClock() {
            const now = new Date();
            const options = { 
                weekday: 'short', 
                day: '2-digit', 
                month: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };
            this.currentDateTime = now.toLocaleDateString('fr-FR', options);
        },
        
        // Écouter les événements globaux
        listenToGlobalEvents() {
            // Écouter les changements d'OF
            window.addEventListener('of-changed', (event) => {
                this.ofNumber = event.detail.ofNumber || '';
                this.updateRollId();
                this.updateOFStatus();
            });
            
            // Écouter les changements de numéro de rouleau
            window.addEventListener('roll-number-changed', (event) => {
                this.rollNumber = event.detail.rollNumber || '001';
                this.updateRollId();
            });
            
            // Écouter les changements de shift
            window.addEventListener('shift-saved', (event) => {
                this.shiftSaved = true;
                this.shiftId = event.detail.shift?.shift_id || '';
                setTimeout(() => { this.shiftSaved = false; }, 3000);
            });
            
            // Écouter les sauvegardes de rouleau
            window.addEventListener('roll-saved', (event) => {
                this.rollSaved = true;
                setTimeout(() => { this.rollSaved = false; }, 3000);
            });
            
            // Écouter les mises à jour de session
            window.addEventListener('session-updated', (event) => {
                if (event.detail.key === 'of' || event.detail.key === 'roll' || event.detail.key === 'shift') {
                    this.loadFromSession();
                }
            });
        },
        
        // Mettre à jour l'ID rouleau
        updateRollId() {
            if (this.ofNumber && this.rollNumber) {
                // Formater le numéro de rouleau avec padding
                const paddedRollNumber = this.rollNumber.toString().padStart(3, '0');
                this.rollId = `${this.ofNumber}_${paddedRollNumber}`;
            } else {
                this.rollId = '';
            }
        },
        
        // Mettre à jour le statut OF
        updateOFStatus() {
            if (this.ofNumber) {
                this.ofStatus = this.ofNumber;
                
                // Ajouter OF découpe si disponible
                const ofDecoupe = window.sessionData?.of?.ofDecoupe;
                if (ofDecoupe) {
                    this.ofStatus += ` → ${ofDecoupe}`;
                }
                
                // Ajouter le profil si disponible
                const profileName = window.sessionData?.profile?.profileName;
                if (profileName) {
                    this.ofStatus += ` (${profileName})`;
                }
            } else {
                this.ofStatus = 'Aucun OF sélectionné';
            }
        },
        
        // Actions
        async saveAll() {
            showNotification('info', 'Sauvegarde en cours...');
            
            try {
                const promises = [];
                
                // Sauvegarder le shift si on a un shiftId
                if (this.shiftId) {
                    const shiftComponent = document.querySelector('[x-data*="shiftForm"]')?._x_dataStack?.[0];
                    if (shiftComponent?.saveShift) {
                        promises.push(shiftComponent.saveShift());
                    }
                }
                
                // Sauvegarder le rouleau si on a un rollId
                if (this.rollId) {
                    promises.push(this.saveRoll());
                }
                
                // Attendre toutes les sauvegardes
                await Promise.all(promises);
                
                showNotification('success', 'Données sauvegardées avec succès');
            } catch (error) {
                showNotification('error', 'Erreur lors de la sauvegarde');
                if (window.DEBUG) console.error('Save error:', error);
            }
        },
        
        // Sauvegarder le rouleau
        async saveRoll() {
            // Collecter toutes les données du rouleau
            const rollData = {
                roll_id: this.rollId,
                shift_id: this.shiftId,
                of_fabrication: this.ofNumber,
                roll_number: parseInt(this.rollNumber),
                // Ajouter les autres données depuis la session
                ...window.sessionData?.roll
            };
            
            try {
                // Utiliser fetch directement comme dans les autres composants V3
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || window.csrfToken || '';
                
                const response = await fetch('/api/rolls/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(rollData)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                window.dispatchEvent(new CustomEvent('roll-saved', { 
                    detail: { roll: data }
                }));
                return data;
            } catch (error) {
                console.error('Erreur sauvegarde rouleau:', error);
                throw error;
            }
        },
        
        async exportData() {
            showNotification('info', 'Export en préparation...');
            // Export non implémenté pour l'instant
        },
        
        toggleDebug() {
            const currentDebug = localStorage.getItem('debug') === 'true';
            localStorage.setItem('debug', !currentDebug);
            location.reload();
        },
        
        // Gérer le changement du numéro de rouleau
        handleRollNumberChange() {
            // Formater avec padding si c'est un nombre
            if (this.rollNumber && !isNaN(this.rollNumber)) {
                this.rollNumber = this.rollNumber.toString().padStart(3, '0');
            }
            
            window.session.save('sticky_roll_number', this.rollNumber);
            this.updateRollId();
            
            // Émettre l'événement
            window.dispatchEvent(new CustomEvent('roll-number-changed', {
                detail: { rollNumber: this.rollNumber }
            }));
        },
        
        // Gérer les changements de données
        handleDataChange() {
            window.session.save('sticky_tube_mass', this.tubeMass);
            window.session.save('sticky_length', this.length);
            window.session.save('sticky_total_mass', this.totalMass);
            window.session.save('sticky_next_tube_mass', this.nextTubeMass);
            
            this.calculateValues();
        },
        
        // Calculer les valeurs dérivées
        calculateValues() {
            // Calculer la masse nette
            if (this.totalMass && this.tubeMass) {
                const total = parseFloat(this.totalMass);
                const tube = parseFloat(this.tubeMass);
                if (!isNaN(total) && !isNaN(tube)) {
                    this.netMass = (total - tube).toFixed(0);
                } else {
                    this.netMass = '--';
                }
            } else {
                this.netMass = '--';
            }
            
            // Calculer le grammage (g/m²)
            if (this.netMass !== '--' && this.length) {
                const net = parseFloat(this.netMass);
                const len = parseFloat(this.length);
                if (!isNaN(net) && !isNaN(len) && len > 0) {
                    // Formule : (masse nette / longueur) / largeur
                    // Largeur du profil à récupérer depuis la session
                    const width = window.sessionData?.profile?.width || 1.35; // 1.35m par défaut
                    this.grammage = ((net / len) / width).toFixed(1);
                } else {
                    this.grammage = '--';
                }
            } else {
                this.grammage = '--';
            }
        }
    };
}

// Export global pour Alpine
window.stickyBar = stickyBar;