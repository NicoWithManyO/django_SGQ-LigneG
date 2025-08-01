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
            
            // Cleanup se fera automatiquement quand le composant est détruit
        },
        
        // Charger depuis la session
        loadFromSession() {
            const ofData = window.sessionData?.of || {};
            const rollData = window.sessionData?.roll || {};
            const shiftData = window.sessionData?.shift || {};
            
            this.ofNumber = ofData.ofEnCours || '';
            this.rollNumber = rollData.rollNumber || '001';
            this.shiftId = shiftData.shiftId || '';
            
            this.updateRollId();
            this.updateOFStatus();
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
                const response = await window.api.post('/api/rolls/', rollData);
                window.dispatchEvent(new CustomEvent('roll-saved', { 
                    detail: { roll: response }
                }));
                return response;
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
        }
    };
}

// Export global pour Alpine
window.stickyBar = stickyBar;