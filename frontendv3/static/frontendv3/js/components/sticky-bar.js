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
        rollNumber: '',
        ofNumber: '',
        shiftId: '',
        rollSaved: false,
        shiftSaved: false,
        rollStatus: '', // '', 'ok', 'nok'
        rollIdExists: null, // null, true, false
        checkingRollId: false,
        
        // Données du rouleau
        tubeMass: '',
        length: '',
        totalMass: '',
        netMass: '',
        grammage: '',
        nextTubeMass: '',
        
        // Specs du profil et statut grammage
        profileSpecs: null,
        grammageStatus: '', // '', 'ok', 'alert', 'nok'
        
        // Timer pour l'horloge
        clockTimer: null,
        
        // État pour le bouton de sauvegarde
        rollConformityStatus: 'CONFORME',
        allThicknessesFilled: false,
        operatorId: '',
        shiftDate: '',
        vacation: '',
        
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
            
            // Watchers pour auto-save dans la session uniquement
            // Le calcul et l'émission d'événements se feront au blur
            this.$watch('tubeMass', () => window.session.save('sticky_tube_mass', this.tubeMass));
            this.$watch('length', () => window.session.save('sticky_length', this.length));
            this.$watch('totalMass', () => window.session.save('sticky_total_mass', this.totalMass));
            this.$watch('nextTubeMass', () => window.session.save('sticky_next_tube_mass', this.nextTubeMass));
            
            // Cleanup se fera automatiquement quand le composant est détruit
        },
        
        // Charger depuis la session
        loadFromSession() {
            const ofData = window.sessionData?.of || {};
            const rollData = window.sessionData?.roll || {};
            const shiftData = window.sessionData?.shift || {};
            
            this.ofNumber = ofData.ofEnCours || '';
            this.rollNumber = window.sessionData?.sticky_roll_number || rollData.rollNumber || '';
            this.shiftId = shiftData.shiftId || '';
            
            // Charger les données du shift
            this.operatorId = shiftData.operatorId || '';
            this.shiftDate = shiftData.date || '';
            this.vacation = shiftData.vacation || '';
            
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
                // Appliquer automatiquement la baguette magique au changement d'OF
                if (this.ofNumber) {
                    this.fetchNextRollNumber();
                }
            });
            
            // Écouter les changements de numéro de rouleau
            window.addEventListener('roll-number-changed', (event) => {
                this.rollNumber = event.detail.rollNumber || '';
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
            
            // Écouter les changements de profil pour récupérer les specs
            window.addEventListener('profile-changed', (event) => {
                if (event.detail && event.detail.profileSpecs) {
                    this.profileSpecs = event.detail.profileSpecs;
                    // Revérifier le statut du grammage avec les nouvelles specs
                    this.checkGrammageStatus();
                }
            });
            
            // Écouter les changements de conformité
            window.addEventListener('roll-conformity-changed', (event) => {
                console.log('Conformity changed:', event.detail);
                
                // Mettre à jour le statut de conformité et l'état des épaisseurs
                this.rollConformityStatus = event.detail.status;
                this.allThicknessesFilled = event.detail.allThicknessesFilled || false;
                
                // Si le statut passe à NON_CONFORME, changer l'ID en format OF découpe
                if (event.detail.status === 'NON_CONFORME') {
                    // Vérifier si on n'est pas déjà en format découpe
                    if (!this.rollId.startsWith('9999_')) {
                        // Sauvegarder l'OF et le numéro de rouleau originaux avant de changer
                        window.session.save('original_of', this.ofNumber);
                        window.session.save('original_roll_number', this.rollNumber);
                        this.switchToDiscoveryRollId();
                    }
                }
                // Si le statut repasse à CONFORME, restaurer l'ID normal
                else if (event.detail.status === 'CONFORME') {
                    // Restaurer l'OF et le numéro originaux depuis la session
                    const originalOF = window.sessionData?.original_of;
                    const originalRollNumber = window.sessionData?.original_roll_number;
                    
                    if (originalOF && originalRollNumber) {
                        this.ofNumber = originalOF;
                        this.rollNumber = originalRollNumber;
                        this.updateRollId();
                        this.rollStatus = 'ok';
                        
                        // Nettoyer les données temporaires
                        window.session.remove('original_of');
                        window.session.remove('original_roll_number');
                    }
                }
            });
            
            // Écouter les changements de shift pour récupérer les données
            window.addEventListener('shift-data-changed', (event) => {
                if (event.detail) {
                    this.operatorId = event.detail.operatorId || '';
                    this.shiftDate = event.detail.date || '';
                    this.vacation = event.detail.vacation || '';
                }
            });
        },
        
        // Mettre à jour l'ID rouleau
        updateRollId() {
            if (this.ofNumber && this.rollNumber && this.rollNumber.toString().trim() !== '') {
                // Formater le numéro de rouleau avec padding
                const paddedRollNumber = this.rollNumber.toString().padStart(3, '0');
                this.rollId = `${this.ofNumber}_${paddedRollNumber}`;
                this.checkRollIdExists();
            } else {
                this.rollId = '--';
                this.rollIdExists = null;
            }
        },
        
        // Vérifier si l'ID rouleau existe en base
        async checkRollIdExists() {
            if (!this.rollId) {
                this.rollIdExists = null;
                return;
            }
            
            this.checkingRollId = true;
            try {
                const response = await fetch(`/production/api/rolls/check-id/?roll_id=${this.rollId}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                this.rollIdExists = data.exists;
            } catch (error) {
                console.error('Erreur vérification ID:', error);
                this.rollIdExists = null;
            } finally {
                this.checkingRollId = false;
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
        
        // Récupérer le prochain numéro de rouleau disponible
        async fetchNextRollNumber() {
            if (!this.ofNumber) {
                showNotification('warning', 'Aucun OF sélectionné');
                return;
            }
            
            try {
                const response = await fetch(`/production/api/rolls/next-number/?of=${this.ofNumber}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const data = await response.json();
                this.rollNumber = data.next_number;
                this.handleRollNumberChange();
                
                showNotification('success', `Prochain numéro : ${data.next_number}`);
            } catch (error) {
                showNotification('error', 'Erreur lors de la récupération du numéro');
                if (window.DEBUG) console.error('Fetch next number error:', error);
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
                
                const response = await fetch('/production/api/rolls/', {
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
            // Ne formater que si le champ n'est pas vide
            if (this.rollNumber && this.rollNumber.toString().trim() !== '') {
                // Formater avec padding si c'est un nombre
                if (!isNaN(this.rollNumber)) {
                    this.rollNumber = this.rollNumber.toString().padStart(3, '0');
                }
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
        
        // Gérer le blur des champs (recalcul et émission d'événements)
        handleFieldBlur() {
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
                    // Formule : masse nette / longueur = g/m linéaire
                    // Pour un produit en rouleau, le grammage est en g/m linéaire
                    this.grammage = (net / len).toFixed(1);
                    debug(`Grammage calc: ${net}g / ${len}m = ${this.grammage} g/m`);
                } else {
                    this.grammage = '--';
                }
            } else {
                this.grammage = '--';
            }
            
            // Vérifier le statut du grammage
            this.checkGrammageStatus();
        },
        
        // Basculer vers l'ID rouleau de découpe
        switchToDiscoveryRollId() {
            // Format : 9999_JJMMAA
            const now = new Date();
            const day = now.getDate().toString().padStart(2, '0');
            const month = (now.getMonth() + 1).toString().padStart(2, '0');
            const year = now.getFullYear().toString().slice(-2);
            
            this.rollId = `9999_${day}${month}${year}`;
            this.rollStatus = 'nok';
            
            // Sauvegarder dans la session
            window.session.save('sticky_roll_id', this.rollId);
            
            // Émettre un événement pour informer les autres composants
            window.dispatchEvent(new CustomEvent('roll-id-changed', {
                detail: { 
                    rollId: this.rollId,
                    isDiscovery: true
                }
            }));
            
            debug(`Roll ID switched to discovery format: ${this.rollId}`);
        },
        
        // Vérifier le statut du grammage par rapport aux specs
        checkGrammageStatus() {
            // Si pas de grammage calculé ou pas de specs
            if (this.grammage === '--' || !this.profileSpecs) {
                // Si le statut change, émettre l'événement
                if (this.grammageStatus !== '') {
                    this.grammageStatus = '';
                    window.dispatchEvent(new CustomEvent('grammage-status-changed', {
                        detail: { status: '', value: null }
                    }));
                }
                return;
            }
            
            // Chercher la spec "Masse Surfacique Globale" (en g/m²)
            // Ne PAS utiliser "Masse Surfacique" qui est en g/25cm²
            const spec = this.profileSpecs.find(s => 
                s.name === 'Masse Surfacique Globale'
            );
            
            if (!spec) {
                this.grammageStatus = '';
                debug('Spec "Masse Surfacique Globale" non trouvée dans:', this.profileSpecs);
                return;
            }
            
            debug('Spec trouvée:', spec);
            
            const value = parseFloat(this.grammage);
            if (isNaN(value)) {
                this.grammageStatus = '';
                return;
            }
            
            // Vérifier selon les 4 seuils (comme pour les épaisseurs)
            let newStatus = 'ok';
            if (spec.value_min !== null && value < spec.value_min) {
                newStatus = 'nok';
            } else if (spec.value_min_alert !== null && value < spec.value_min_alert) {
                newStatus = 'alert';
            } else if (spec.value_max !== null && value > spec.value_max) {
                newStatus = 'nok';
            } else if (spec.value_max_alert !== null && value > spec.value_max_alert) {
                newStatus = 'alert';
            }
            
            // Si le statut a changé, émettre un événement
            if (this.grammageStatus !== newStatus) {
                this.grammageStatus = newStatus;
                window.dispatchEvent(new CustomEvent('grammage-status-changed', {
                    detail: { status: newStatus, value: value }
                }));
            }
            
            debug('Grammage status:', this.grammageStatus, 'for value:', value);
        },
        
        // Propriétés calculées pour le bouton de sauvegarde
        get hasRequiredShiftData() {
            return this.operatorId && this.shiftDate && this.vacation;
        },
        
        get hasGrammage() {
            return this.grammage !== '--' && this.grammage !== '';
        },
        
        get canSaveRoll() {
            // Toujours besoin des données du poste et du grammage
            if (!this.hasRequiredShiftData || !this.hasGrammage) {
                return false;
            }
            
            // Si conforme, besoin de toutes les épaisseurs
            if (this.rollConformityStatus === 'CONFORME') {
                debug(`Checking canSaveRoll: allThicknessesFilled=${this.allThicknessesFilled}`);
                return this.allThicknessesFilled;
            }
            
            // Si non conforme, on peut sauver même sans toutes les épaisseurs
            return true;
        },
        
        get saveButtonTooltip() {
            // Si le bouton est actif, pas de tooltip
            if (this.canSaveRoll) {
                return '';
            }
            
            // Sinon, lister ce qui manque
            const missing = [];
            
            if (!this.operatorId) missing.push('Opérateur requis');
            if (!this.shiftDate) missing.push('Date requise');
            if (!this.vacation) missing.push('Vacation requise');
            if (!this.hasGrammage) missing.push('Grammage requis (masse + longueur)');
            
            if (this.rollConformityStatus === 'CONFORME' && !this.allThicknessesFilled) {
                debug(`Tooltip check: conformityStatus=${this.rollConformityStatus}, allThicknessesFilled=${this.allThicknessesFilled}`);
                missing.push('Toutes les épaisseurs requises');
            }
            
            debug(`SaveButtonTooltip: ${missing.join(' • ')}`);
            return missing.join(' • ');
        }
    };
}

// Export global pour Alpine
window.stickyBar = stickyBar;