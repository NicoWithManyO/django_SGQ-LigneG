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
        
        // Statut QC temps réel
        currentQcStatus: '',
        
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
            this.rollNumber = window.sessionData?.sticky_roll_number || '';
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
            
            // Charger le statut QC initial
            this.currentQcStatus = window.sessionData?.qc_status || '';
            
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
                debug('Conformity changed:', event.detail);
                
                // Mettre à jour le statut de conformité et l'état des épaisseurs
                this.rollConformityStatus = event.detail.status;
                this.allThicknessesFilled = event.detail.allThicknessesFilled || false;
                
                // Mettre à jour l'ID selon le statut
                this.updateRollId();
            });
            
            // Écouter les changements de shift pour récupérer les données
            window.addEventListener('shift-data-changed', (event) => {
                if (event.detail) {
                    this.operatorId = event.detail.operatorId || '';
                    this.shiftDate = event.detail.date || '';
                    this.vacation = event.detail.vacation || '';
                    this.shiftId = event.detail.shiftId || '';
                }
            });
            
            // Écouter les changements de statut QC
            window.addEventListener('qc-status-changed', (event) => {
                if (event.detail && event.detail.status !== undefined) {
                    this.currentQcStatus = event.detail.status;
                    debug('QC status updated:', this.currentQcStatus);
                }
            });
        },
        
        // Mettre à jour l'ID rouleau
        updateRollId() {
            if (this.rollConformityStatus === 'NON_CONFORME') {
                // Utiliser OF découpe avec date
                const ofDecoupe = window.sessionData?.of?.ofDecoupe || '9999';
                const now = new Date();
                const day = now.getDate().toString().padStart(2, '0');
                const month = (now.getMonth() + 1).toString().padStart(2, '0');
                const year = now.getFullYear().toString().slice(-2);
                this.rollId = `${ofDecoupe}_${day}${month}${year}`;
                this.rollStatus = 'nok';
            } else if (this.ofNumber && this.rollNumber && this.rollNumber.toString().trim() !== '') {
                // Utiliser OF en cours avec numéro de rouleau
                const paddedRollNumber = this.rollNumber.toString().padStart(3, '0');
                this.rollId = `${this.ofNumber}_${paddedRollNumber}`;
                this.rollStatus = 'ok';
            } else {
                this.rollId = '--';
                this.rollIdExists = null;
                return;
            }
            this.checkRollIdExists();
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
                debug('Erreur vérification ID:', error);
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
                debug('Fetch next number error:', error);
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
                debug('Save error:', error);
            }
        },
        
        // Sauvegarder le rouleau
        async saveRoll() {
            if (!this.canSaveRoll) {
                showNotification('warning', this.saveButtonTooltip);
                return;
            }
            
            // Utiliser la modal si disponible
            if (window.modalBuilders && window.modalBuilders.buildRollConfirmation) {
                // Préparer les données pour la modal
                const rollData = {
                    rollId: this.rollId,
                    status: this.rollConformityStatus,
                    length: this.length,
                    netWeight: this.netMass,
                    grammage: this.grammage,
                    defectCount: 0
                };
                
                // Compter les défauts
                const defectsData = window.sessionData?.v3_production?.roll?.defects || {};
                let defectCount = 0;
                for (const cellDefects of Object.values(defectsData)) {
                    defectCount += cellDefects.length;
                }
                rollData.defectCount = defectCount;
                
                // Ajouter les données QC si disponibles
                const qcData = window.sessionData?.v3_production || {};
                if (qcData.qc_micromaire_g || qcData.qc_micromaire_d) {
                    const avgLeft = this._calcAvg(qcData.qc_micromaire_g || []);
                    const avgRight = this._calcAvg(qcData.qc_micromaire_d || []);
                    if (avgLeft) {
                        rollData.qcMicromaire = avgLeft.toFixed(1);
                        rollData.qcMicromaireUnit = 'μm';
                    } else if (avgRight) {
                        rollData.qcMicromaire = avgRight.toFixed(1);
                        rollData.qcMicromaireUnit = 'μm';
                    }
                }
                
                if (qcData.qc_masse_surfacique_gg || qcData.qc_masse_surfacique_gc || 
                    qcData.qc_masse_surfacique_dc || qcData.qc_masse_surfacique_dd) {
                    const avgMasse = this._calcAvg([
                        qcData.qc_masse_surfacique_gg,
                        qcData.qc_masse_surfacique_gc,
                        qcData.qc_masse_surfacique_dc,
                        qcData.qc_masse_surfacique_dd
                    ]);
                    if (avgMasse) {
                        rollData.qcMasseSurf = avgMasse.toFixed(1);
                        rollData.qcMasseSurfUnit = 'g/25cm²';
                    }
                }
                
                // Utiliser le statut QC temps réel
                rollData.qcStatus = this.currentQcStatus || '';
                debug('QC Status for modal:', rollData.qcStatus);
                
                // Construire le contenu de la modal
                const modalConfig = window.modalBuilders.buildRollConfirmation(rollData);
                
                // Ajouter l'action de confirmation
                modalConfig.confirmAction = async () => {
                    // Récupérer le commentaire depuis la modal
                    const modalElement = document.querySelector('[x-data*="confirmModal"]');
                    let comment = '';
                    if (modalElement && modalElement._x_dataStack) {
                        const modalComponent = modalElement._x_dataStack[0];
                        comment = modalComponent.modalConfig.commentValue || '';
                    }
                    await this._performSaveRoll(comment);
                };
                
                // Obtenir la référence au composant modal
                const modalElement = document.querySelector('[x-data*="confirmModal"]');
                if (modalElement && modalElement._x_dataStack) {
                    const modalComponent = modalElement._x_dataStack[0];
                    modalComponent.show(modalConfig);
                    return;
                }
            }
            
            // Si pas de modal, sauvegarder directement
            await this._performSaveRoll();
        },
        
        // Fonction interne pour effectuer la sauvegarde
        async _performSaveRoll(comment = '') {
            
            try {
                showNotification('info', 'Sauvegarde du rouleau...');
                
                // Préparer les données minimales
                const rollData = {
                    shift_id_str: this.shiftId,
                    tube_mass: parseFloat(this.tubeMass) || null,
                    total_mass: parseFloat(this.totalMass) || null,
                    length: parseFloat(this.length) || null,
                    status: this.rollConformityStatus,
                    comment: comment || ''
                };
                
                // Toujours envoyer le roll_id
                rollData.roll_id = this.rollId;
                
                // Pour CONFORME seulement, envoyer le roll_number (entier)
                if (this.rollConformityStatus === 'CONFORME') {
                    rollData.roll_number = parseInt(this.rollNumber);
                }
                // Pour NON_CONFORME, pas de roll_number (le backend gère)
                
                // L'OF sera extrait automatiquement du roll_id par le backend
                
                // Le backend va récupérer les épaisseurs et défauts depuis la session
                
                debug('Données à envoyer:', rollData);
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                const response = await fetch('/production/api/rolls/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(rollData)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    debug('Erreur API:', error);
                    throw new Error(error.error || error.detail || `HTTP ${response.status}`);
                }
                
                const savedRoll = await response.json();
                debug('Réponse du backend:', savedRoll);
                
                // Appliquer l'état renvoyé par le backend
                if (savedRoll.next_roll_data) {
                    // Si on était en mode découpe et qu'on nous renvoie un OF normal
                    if (this.ofNumber === '9999' && savedRoll.next_roll_data.of_number !== '9999') {
                        // Restaurer l'OF original si disponible
                        const originalOF = window.sessionData?.original_of;
                        if (originalOF) {
                            this.ofNumber = originalOF;
                            window.session.remove('original_of');
                            window.session.remove('original_roll_number');
                        }
                    } else {
                        this.ofNumber = savedRoll.next_roll_data.of_number || this.ofNumber;
                    }
                    
                    this.rollNumber = savedRoll.next_roll_data.roll_number;
                    this.tubeMass = savedRoll.next_roll_data.tube_mass || '';
                    this.nextTubeMass = '';
                    this.totalMass = '';
                    // Récupérer la longueur cible depuis la session
                    const targetLength = window.sessionData?.of?.targetLength;
                    this.length = targetLength ? String(targetLength) : '';
                    this.calculateValues();
                    this.handleRollNumberChange();
                    this.updateOFStatus();
                }
                
                showNotification('success', `Rouleau ${savedRoll.roll_id} sauvegardé`);
                
                // Émettre l'événement de succès
                window.dispatchEvent(new CustomEvent('roll-saved', { 
                    detail: { roll: savedRoll }
                }));
                
                // Informer les autres composants de se réinitialiser
                window.dispatchEvent(new CustomEvent('roll-reset'));
                
                return savedRoll;
                
            } catch (error) {
                debug('Erreur sauvegarde rouleau:', error);
                showNotification('error', `Erreur: ${error.message}`);
                throw error;
            }
        },
        
        async exportData() {
            showNotification('info', 'Export en préparation...');
            // Export non implémenté pour l'instant
        },
        
        // Vider toutes les données sauf la partie ordre de fabrication
        clearAllExceptOF() {
            // Confirmation avant de vider
            if (!confirm('Êtes-vous sûr de vouloir vider toutes les données (sauf les OF) ?')) {
                return;
            }
            
            // Sauvegarder les données OF actuelles
            const currentOF = {
                ofEnCours: window.sessionData?.of?.ofEnCours || '',
                ofDecoupe: window.sessionData?.of?.ofDecoupe || '',
                targetLength: window.sessionData?.of?.targetLength || 0
            };
            
            // Vider toutes les données en les mettant à null/vide
            const emptyData = {
                // Shift
                shift: {
                    operatorId: '',
                    date: new Date().toISOString().split('T')[0],
                    vacation: '',
                    shiftId: '',
                    startTime: '',
                    machineStartedStart: false,
                    lengthStart: '',
                    endTime: '',
                    machineStartedEnd: false,
                    lengthEnd: '',
                    comments: ''
                },
                // Rouleau
                roll: {
                    defects: {},
                    thicknessValues: {},
                    rattrapages: {}
                },
                // QC
                qc_micromaire_g: ['', '', ''],
                qc_micromaire_d: ['', '', ''],
                qc_masse_surfacique_gg: '',
                qc_masse_surfacique_gc: '',
                qc_masse_surfacique_dc: '',
                qc_masse_surfacique_dd: '',
                qc_extrait_sec: '',
                qc_extrait_time: '--:--',
                qc_loi: false,
                qc_loi_time: '--:--',
                qc_status: 'pending',
                // Checklist
                checklist: {
                    items: {},
                    responses: {},
                    comments: {},
                    signature: '',
                    signatureTime: ''
                },
                // Temps perdus
                lost_time_entries: [],
                // Sticky bar - utiliser les vraies clés
                sticky_roll_number: '',
                sticky_tube_mass: '',
                sticky_next_tube_mass: '',
                sticky_total_mass: '',
                sticky_length: currentOF.targetLength ? String(currentOF.targetLength) : '', // Garder la longueur liée à l'OF
                // OF - on garde les valeurs actuelles
                of: currentOF
            };
            
            // Envoyer tout d'un coup
            window.session.patch(emptyData);
            
            // Recharger la page après un court délai pour laisser le temps à la sauvegarde
            setTimeout(() => {
                window.location.reload();
            }, 500);
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
        
        // Helper pour remplir automatiquement TOUT
        fillMassFields() {
            // 1. Remplir les épaisseurs avec rollGridUtils
            if (window.rollGridUtils && window.rollGridUtils.fillRandom) {
                window.rollGridUtils.fillRandom();
            }
            
            // 2. Remplir masse tube si vide
            if (!this.tubeMass) {
                // Masse tube autour de 900g avec variation aléatoire ±50g
                const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
                this.tubeMass = String(900 + variation);
            }
            
            // 3. Calculer la masse totale pour obtenir un grammage d'environ 80 g/m
            if (this.length) {
                const targetGrammage = 80; // g/m
                const len = parseFloat(this.length);
                const tube = parseFloat(this.tubeMass);
                
                if (!isNaN(len) && !isNaN(tube) && len > 0) {
                    // Masse nette = longueur * grammage cible
                    const netMass = len * targetGrammage;
                    // Masse totale = masse tube + masse nette
                    const totalMass = tube + netMass;
                    // Ajouter une petite variation aléatoire (±5%)
                    const variation = 1 + (Math.random() * 0.1 - 0.05);
                    this.totalMass = String(Math.round(totalMass * variation));
                }
            }
            
            // 4. Remplir masse tube suivante
            if (!this.nextTubeMass) {
                const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
                this.nextTubeMass = String(900 + variation);
            }
            
            // 5. Remplir les contrôles qualité
            window.dispatchEvent(new CustomEvent('fill-qc-random'));
            
            // 6. Remplir la checklist avec signature - attendre un peu pour que les composants soient chargés
            setTimeout(() => {
                const checklistComponent = document.querySelector('[x-data*="checklist"]');
                if (checklistComponent && checklistComponent._x_dataStack && window.testHelpers && window.testHelpers.fillChecklist) {
                    const checklistData = checklistComponent._x_dataStack[0];
                    window.testHelpers.fillChecklist(checklistData);
                }
            }, 100);
            
            // Sauvegarder et recalculer
            this.handleDataChange();
            
            showNotification('success', '🎩 Baguette magique : Tout est rempli !');
        },
        
        // Helper pour générer une masse tube suivante
        fillNextTubeMass() {
            // Générer une masse tube autour de 900g avec variation aléatoire ±50g
            const variation = Math.floor(Math.random() * 101) - 50; // -50 à +50
            this.nextTubeMass = String(900 + variation);
            
            // Sauvegarder
            window.session.save('sticky_next_tube_mass', this.nextTubeMass);
            
            showNotification('info', `Masse tube suivante : ${this.nextTubeMass}g`);
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
        
        
        // Vérifier le statut du grammage par rapport aux specs
        // Helper pour calculer la moyenne d'un tableau
        _calcAvg(values) {
            if (!values || !Array.isArray(values)) return null;
            const validValues = values.filter(v => v !== null && v !== undefined && !isNaN(v));
            if (validValues.length === 0) return null;
            return validValues.reduce((sum, v) => sum + parseFloat(v), 0) / validValues.length;
        },
        
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